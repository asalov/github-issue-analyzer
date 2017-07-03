import pandas as pd
from githubanalyzer.preprocessor import TextPreprocessor
from githubanalyzer.cleaner import DataCleaner
from githubanalyzer.mongodb import MongoDB

# Constants
FILE_PATH = '../data/'
OUTPUT_FILE = FILE_PATH + 'issues_processed.json'

# Process input and save output
def process_data():
    mongo = MongoDB('github')
    df = pd.DataFrame(list(mongo.get_all('issues')))
    
    cleaner = DataCleaner()
    
    df['title'] = prepare_text(df['title'])
    df = cleaner.remove_empty(df, ['title'])
    
    df = df.filter(items=['id', 'title'])
    
    mongo.save('processed', df)
    df.to_json(OUTPUT_FILE, orient='records')
    
# Preprocess text
def prepare_text(dataset): 
    processor = TextPreprocessor()
   
    data = processor.prepare(dataset)
    data = [' '.join(item) for item in data]
    
    return data
          
# Run application        
if __name__ == '__main__':
    process_data()