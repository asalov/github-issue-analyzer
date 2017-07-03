import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans, KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
from sklearn.metrics import silhouette_score, calinski_harabaz_score
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.feature_selection import mutual_info_classif
from sklearn.externals import joblib
from scipy import sparse
from scipy.spatial.distance import cdist, pdist

class DocumentClusterer:
    
    # Extract features from document dataset
    def extract_features(self, data, num_features=None, max_freq=0.75, min_count=10, 
                         stopwords=True, ngram_range=(1,3)):
        
        if isinstance(stopwords, list):
            stop = stopwords
        elif stopwords is True:
            stop = 'english'
        else:
            stop = None
        
        self.vectorizer = TfidfVectorizer(stop_words=stop, ngram_range=ngram_range, 
                                 max_df=max_freq, min_df=min_count, max_features=num_features,
                                 sublinear_tf=True)
        self.features = self.vectorizer.fit_transform(item for item in data)
  
    # Transform document to vector (using existing vocabulary)
    def vectorize(self, data):
        return self.vectorizer.transform(item for item in data)
        
    # Cluster documents
    def cluster(self, features, num_clusters=2, max_iterations=300, logging=False):
        self.model = KMeans(num_clusters, max_iter=max_iterations, verbose=logging)
        self.model.fit(features)
        self.clusters = self.model.labels_
    
    # Cluster documents using batches
    def batch_cluster(self, features, num_clusters=2, batch_size=500, max_iterations=300, logging=False):
        self.model = MiniBatchKMeans(num_clusters, max_iter=max_iterations, 
                                     batch_size=batch_size, verbose=logging)
        self.model.fit(features)
        self.clusters = self.model.labels_
        
    # Predict cluster assignment
    def predict(self, features, level=1, scale=False):
        if scale is True:
            features = self.scale_func.transform(features)
        
        if level > 1:
            top_level = self.model.predict(features)
            assignment = list()
            
            for ind, item in enumerate(top_level):
                item_assignment = list()
                item_assignment.append(item)
                
                f = features[ind, None, :]
                second_level = self.hierarchy[item]['model'].predict(f)
                subcluster = second_level[0]
                item_assignment.append(subcluster)
                
                if level > 2 and subcluster in self.hierarchy[item]:
                    third_level = self.hierarchy[item][subcluster]['model'].predict(f)
                    item_assignment.append(third_level[0])
                        
                assignment.append(item_assignment)
            
            return assignment
        
        return self.model.predict(features)
    
    # Build hierarchical cluster tree
    def build_hierarchy(self, features, cluster_indices, num_clusters=5, max_cluster_size=100):
        options = {
            'max_level':3,
            'max_cluster_size': max_cluster_size
        }
        
        self.hierarchy = dict()
        clusters = dict()
        
        for i in range(len(set(cluster_indices))):
            clusters[i] = list()
            
        for ind, item in enumerate(cluster_indices):
            clusters[item].append((ind, features[ind]))
        
        for cluster in clusters:
            self.hierarchy[cluster] = dict()
            options['cluster_index'] = cluster
            options['level'] = 1
            
            self.subcluster(clusters[cluster], num_clusters, options)
            options.pop('subcluster_index', None)
            
    # Divide clusters into subclusters
    def subcluster(self, features, num_clusters, options):
        options['level'] += 1
        subcluster_indices = list()
        
        model = KMeans(num_clusters)
        f = [item[1] for item in features]
        model.fit(f)
        
        if 'subcluster_index' in options:
            self.hierarchy[options['cluster_index']][options['subcluster_index']]['model'] = model
            self.hierarchy[options['cluster_index']][options['subcluster_index']]['features'] = features          
        else:
            self.hierarchy[options['cluster_index']]['model'] = model
            self.hierarchy[options['cluster_index']]['features'] = features
            
        indices = model.labels_
        cluster_sizes = Counter(indices)
        
        for index in cluster_sizes:
            if cluster_sizes[index] > options['max_cluster_size']:
                subcluster_indices.append(index)
        
        for index in subcluster_indices:
            if options['level'] >= options['max_level']:
                return
            
            self.hierarchy[options['cluster_index']][index] = dict()
            options['subcluster_index'] = index
                
            sub_features = [features[ind] for ind, item in enumerate(indices) if item == index]
            
            self.subcluster(sub_features, num_clusters, options)
            options['level'] -= 1
            
    # Reduce data dimensionality
    def scale_data(self, features, num_dimensions=2, save_features=False, algorithm='arpack', random_seed=None):
        svd = TruncatedSVD(n_components=num_dimensions, algorithm=algorithm, random_state=random_seed)
        self.scale_func = make_pipeline(svd, Normalizer(copy=False))
        scaled = self.scale_func.fit_transform(features)
        
        if save_features is True:
            self.scaled_features = scaled
            
        return scaled
    
    # Evaluate clustering accuracy
    def score_clustering(self, features, sample_size=None):
        sil_score = silhouette_score(features, self.clusters, sample_size=sample_size)
        ch = calinski_harabaz_score(features, self.clusters)
        print('Silhouette score: %f' % sil_score)
        print('Calinski-Harabaz score: %f' % ch)
    
    # Determine number of clusters which produces most accurate clustering
    def determine_num_clusters(self, features, k_range=(2,20), sample_size=None, batch=False, batch_size=500):
        for i in range(k_range[0], k_range[1] + 1):
            print('Results for %d clusters' % i)
            
            if batch is not True:
                self.cluster(features, num_clusters=i)
            else:
                self.batch_cluster(features, num_clusters=i, batch_size=batch_size)
                
            self.score_clustering(features, sample_size=sample_size)
            print('------------')
    
    # Get documents closest to data point
    def closest_docs(self, point, docs, num_docs=5):
        distances = euclidean_distances(point, docs)
        
        return distances.argsort()[:, :num_docs]
    
    # Determine feature predictive power
    def feature_score(self):
        return mutual_info_classif(self.features, self.clusters, discrete_features=True)
    
    # Visualize clusters
    def visualize_data(self, features):
        if features.shape[1] > 2:
            features = self.scale_data(features, num_dimensions=2)
        
        x = features[:,0]
        y = features[:,1]
        
        labels = self.clusters.tolist()
        df = pd.DataFrame(dict(x=x, y=y,label=labels)) 
        groups = df.groupby('label')
        
        num_clusters = len(groups)
        
        colors = plt.get_cmap('Set1') 
        plt.style.use('bmh')
        
        fig, ax = plt.subplots(figsize=(17, 9))
        ax.margins(0.05)
        
        for index, cluster in groups:
            ax.plot(cluster.x, cluster.y, label=labels, 
                    color=colors(1.*index/num_clusters), marker='o', 
                    linestyle='', ms=5, mec='#000000', mew=0.3)
        
        plt.title('Clustering results - %d clusters' % num_clusters)
        plt.show()
    
    # Save clustering class to file
    def save(self, file, keep_stopwords=True):
        if keep_stopwords is False:
            self.vectorizer.stop_words_ = None
            
        joblib.dump(self, file)
        
    # Remove null vectors
    def remove_nulls(self, features):
        features = features.toarray()
        features = features[~np.all(features == 0, axis=1)]
        
        return sparse.csr_matrix(features)
    
    # Determine number of clusters using the Elbow method
    def elbow(self, features, k_range=(2, 20), sample_size=None, batch=False, batch_size=500):
        cluster_range = range(k_range[0], k_range[1] + 1)
        
        if sample_size is not None:
            features = np.array([features[i] for i in sorted(random.sample(range(features.shape[0]), sample_size))])
        
        if batch is not True:
            k_vals = [KMeans(k).fit(features) for k in cluster_range]
        else:
            k_vals = [MiniBatchKMeans(k, batch_size=batch_size).fit(features) for k in cluster_range]
            
        centroids = [model.cluster_centers_ for model in k_vals]
        center_dist = [cdist(features, center, 'euclidean') for center in centroids]
        dist = [np.min(cd, axis=1) for cd in center_dist]
        
        wcss = [sum(d**2) for d in dist]
        tss = sum(pdist(features)**2)/features.shape[0]        
        bss = tss - wcss
        
        fig, ax = plt.subplots(figsize=(17, 9))
        ax.margins(0.05)
        ax.set_xlabel('Number of clusters')
        ax.set_ylabel('Percentage of variance (%)')    
        ax.plot(cluster_range, (bss/tss)*100)
        ax.set_xticks(cluster_range)
        
        plt.style.use('bmh')
        plt.title('Variance depending on number of clusters')
        plt.show()