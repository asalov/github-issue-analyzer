import itertools
import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances
from githubanalyzer.cleaner import DataCleaner
from githubanalyzer.preprocessor import TextPreprocessor

class SolutionFinder:
    
    def __init__(self, clusterer, mongo):
        self.clusterer = clusterer
        self.db = mongo
    
    # Transform issues into vectors
    def vectorize_data(self, data):
        processor = TextPreprocessor()
        processed = processor.prepare(data)
        
        if not processed:
            return None
        
        if isinstance(processed[0], list):
            vector = self.clusterer.vectorize([' '.join(item) for item in processed])
        else:
            vector = self.clusterer.vectorize([' '.join(processed)])
        
        return vector if vector.nnz > 0 else None
        
    # Find similar issues
    def find_similar(self, vector, features, issues, max_results=5, max_dist=0.75):
        closest = self.get_closest(vector, features, num_docs=max_results, threshold=max_dist)
        ids = list()
    
        for item in closest:
            ids.append(issues[item]['id'])
        
        res = list(self.db.get_issues_in_list(ids, {'_id':0}))
        
        for i, item in enumerate(res):
            for index, issue_id in enumerate(ids):              
                if issue_id == item['id']:
                    res[i]['index'] = index
        
        res.sort(key=lambda x: x['index'])
        
        return res
    
    # Get closest documents to point
    def get_closest(self, vector, features, num_docs=5, threshold=0.75):
        distances = euclidean_distances(vector, features)
        
        top = distances.argsort()[:, :num_docs]        
        indices = [index for index in top[0] if distances[:, index] < threshold]
        
        return indices
        
    # Get most upvoted comments
    def get_top_comments(self, issues, num_comments=5, threshold=1):
        comments = [item['issue_comments'] for item in issues]
        all_comments = list(itertools.chain.from_iterable(comments))
        
        if not all_comments:
            return list()
        
        cleaner = DataCleaner()
        comm = cleaner.clean(pd.DataFrame(all_comments), ['body'])
        comm = cleaner.filter_english(comm, ['body'])
        
        comm.loc[:, 'positive_score'] = self.calculate_score(comm['reactions'])
        top = comm.sort_values('positive_score', ascending=False)[:num_comments]
        top = top[top['positive_score'] >= threshold]
        
        return top.to_dict(orient='records')

    # Calculate comment score    
    def calculate_score(self, comments):
        scores = list()
        
        for comment in comments:
            score = 0
            
            score += comment['+1']
            score += comment['hooray']
            score += comment['heart']
            score -= comment['-1']
            score -= comment['confused']
            score -= comment['laugh']
            
            scores.append(score)
            
        return scores       