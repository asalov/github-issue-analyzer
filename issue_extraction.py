from sklearn.externals import joblib
from githubanalyzer.mongodb import MongoDB
from githubanalyzer.extractor import IssueExtractor

# Constants
FILE_PATH = '../data/'
OUTPUT_FILE = FILE_PATH + 'analysis_data.csv'
CLUSTERING_MODEL_FILE = FILE_PATH + 'clustering_model.pkl'

# Process input and save output
def process_data():
    mongo = MongoDB('github')
    clusterer = joblib.load(CLUSTERING_MODEL_FILE)
    
    extractor = IssueExtractor(clusterer, mongo)
    
    num_terms = 10
    num_titles = 5
    
    terms = extractor.extract_terms(num_terms=num_terms)
    titles = extractor.extract_titles(num_titles=num_titles)
    
    extractor.save_data(OUTPUT_FILE, terms, titles)
    
# Run application        
if __name__ == '__main__':
    process_data()