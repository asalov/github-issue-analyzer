import pandas as pd
from githubanalyzer.mongodb import MongoDB
from sklearn.externals import joblib

# Constants
FILE_PATH = '../data/'
CLUSTER_FILE = FILE_PATH + 'issue_clusters.json'
CLUSTERING_MODEL_FILE = FILE_PATH + 'clustering_model.pkl'

# Process input and save output
def process_data():
    clusterer = joblib.load(CLUSTERING_MODEL_FILE)
    mongo = MongoDB('github')

    features = clusterer.scale_data(clusterer.features, num_dimensions=100, save_features=True)
    sample = round((33 / 100) * features.shape[0])
    
    clusterer.cluster(features, num_clusters=30, max_iterations=200, logging=True)
    clusterer.score_clustering(features, sample_size=sample)
    
    # Save clustering class
    clusterer.save(CLUSTERING_MODEL_FILE)

    # Save cluster asignments
    df = pd.read_json(CLUSTER_FILE)
    df.loc[:, 'cluster_index'] = clusterer.clusters
    df.to_json(CLUSTER_FILE, orient='records')
    
    mongo.assign_clusters(clusterer.clusters)
    
# Run application        
if __name__ == '__main__':    
    process_data()    