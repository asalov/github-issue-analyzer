import math
import pandas as pd
from githubanalyzer.clusterer import DocumentClusterer
from githubanalyzer.mongodb import MongoDB

# Constants
FILE_PATH = '../data/'
OUTPUT_FILE = FILE_PATH + 'issue_clusters.json'
CLUSTERING_MODEL_FILE = FILE_PATH + 'clustering_model.pkl'

# Process input and save output
def process_data():
    mongo = MongoDB('github')
    df = pd.DataFrame(list(mongo.get_all('processed')))
    
    # Context-specific stopwords
    stopwords = ['problem', 'issue', 'help', 'bug', 'work']
    
    clusterer = DocumentClusterer()
    clusterer.extract_features(df['title'], stopwords=stopwords,
                               max_freq=0.05, min_count=10, ngram_range=(1,3))
    
    df['title'] = clusterer.features.todense().tolist()       
    not_null = [not all(math.isclose(item, 0.0) for item in array) for array in df['title'].tolist()]
    df = df[not_null]
    
    clusterer.features = clusterer.remove_nulls(clusterer.features)
    clusterer.save(CLUSTERING_MODEL_FILE)
    
    df = df.filter(items=['id'])
    
    mongo.save('clusters', df, needs_conversion=True)
    df.to_json(OUTPUT_FILE, orient='records')
    
# Run application        
if __name__ == '__main__':
    process_data()