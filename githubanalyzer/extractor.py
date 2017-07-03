import csv
import itertools
import random
import pandas as pd
import numpy as np

class IssueExtractor:
    
    def __init__(self, clusterer, mongo):
        self.clusterer = clusterer
        self.db = mongo
    
    # Extract terms from each cluster
    def extract_terms(self, num_terms=10):
        clust = self.clusterer
        feature_names = clust.vectorizer.get_feature_names()
        
        scores = clust.feature_score()
        
        svd = clust.scale_func.get_params()['truncatedsvd']
        original_centers = svd.inverse_transform(clust.model.cluster_centers_)
        centers = original_centers.argsort()[:, ::-1]
        
        clustered_docs = list(zip(clust.features, clust.clusters))
        
        terms = list()
        clusters = list()
        
        for key, val in clustered_docs:
            clusters.append(val)
            array = np.squeeze(key.toarray())
            
            indices = array.nonzero()[0]
            issue_terms = list()
            
            for index in indices:
                issue_terms.append((index, array[index]))
            
            terms.append(issue_terms)
        
        df = pd.DataFrame({'terms': terms, 'clusters': clusters})
        cluster_groups = df.groupby('clusters')
        
        differ_terms = dict()
        sample_terms = dict()
        centroid_terms = dict()
        
        for ind, group in cluster_groups:
            feature_list = list(set(itertools.chain.from_iterable(group['terms'])))
            feature_list.sort(key=lambda x: float(x[1]), reverse=True)
            cluster_terms = set([item[0] for item in feature_list][:30])
            
            index_list = list()
            differ_list = list()
            for i, score in enumerate(scores):
                if i in cluster_terms:
                    index_list.append(i)
                    differ_list.append((feature_names[i], score))
            
            differ_list.sort(key=lambda x: float(x[1]), reverse=True)
            differ_terms[ind] = [item[0] for item in differ_list][:num_terms] if len(differ_list) > num_terms else differ_list
            
            cluster_centroid = list()
            for i in centers[ind, :num_terms]:
                index_list.append(i)
                cluster_centroid.append(feature_names[i])
            
            centroid_terms[ind] = cluster_centroid
            
            sample_list = set([item[0] for item in feature_list if item[0] not in set(index_list)])
            num_items = len(sample_list)
            
            sample_size = num_terms if num_terms < num_items else num_items
            sample = random.sample(sample_list, sample_size)         
            sample_terms[ind] = [feature_names[index] for index in sample]
        
        all_terms = dict()
        all_terms['differ'] = differ_terms
        all_terms['internal'] = centroid_terms
        all_terms['random'] = sample_terms
        
        return all_terms
    
    # Extract issue titles from each cluster
    def extract_titles(self, num_titles=5):
        titles = dict()
        
        doc_indices = self.clusterer.closest_docs(self.clusterer.model.cluster_centers_, 
                                             self.clusterer.scaled_features, num_docs=num_titles)
        titles['closest'] = self.get_doc_ids(doc_indices)
        titles['random'] = self.get_sample_ids(titles['closest'], sample_size=num_titles)
        
        return titles

    # Get document ids
    def get_doc_ids(self, doc_indices):
        res = list(self.db.get_all('clusters'))
        
        title_ids = dict()
        
        for  key, val in enumerate(doc_indices):
            doc_ids = list()
            
            for index in val:
                doc_ids.append(res[index]['id'])
            
            title_ids[key] = doc_ids
        
        return title_ids
    
    # Get random sample of issue ids from each cluster
    def get_sample_ids(self, selected_ids=None, sample_size=5):
        num_clusters = self.db.cluster_count()
        samples = dict()
        
        for index in range(num_clusters):
            res = list(self.db.get_cluster(index))
            
            if selected_ids is not None:
                issues = [item['id'] for item in res if item['id'] not in selected_ids[index]]
            else:
                issues = [item['id'] for item in res]
            
            ids = random.sample(range(len(issues)), sample_size)
            
            samples[index] = [issues[i] for i in ids]
            
        return samples
    
    # Save data to file
    def save_data(self, file, terms, titles):
        with open(file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f) 
            writer.writerow(['Cluster index', 'Differential terms', 'Internal terms', 
                       'Random terms', 'Closest titles', 'Random titles'])
            
            for ind in range(len(terms['random'])):
                closest_issues = self.db.get_issues_in_list(titles['closest'][ind], {'title':1})
                random_issues = self.db.get_issues_in_list(titles['random'][ind], {'title':1})
                
                closest_titles = [item['title'] for item in closest_issues]
                random_titles = [item['title'] for item in random_issues]
                
                differ_terms = ', '.join(terms['differ'][ind])
                internal_terms = ', '.join(terms['internal'][ind])
                random_terms = ', '.join(terms['random'][ind])
                
                separator = '\n---------------------------\n'
                closest_titles = separator.join(closest_titles)
                random_titles = separator.join(random_titles)
                
                writer.writerow([ind, differ_terms, internal_terms, random_terms,
                                  closest_titles, random_titles]) 