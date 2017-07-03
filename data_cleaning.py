import pandas as pd
from githubanalyzer.cleaner import DataCleaner
from githubanalyzer.mongodb import MongoDB

# Constants
FILE_PATH = '../data/'
OUTPUT_FILE = FILE_PATH + 'issues_clean.json'

# Process input and save output
def process_data():
    mongo = MongoDB('github')
    df = pd.DataFrame(list(mongo.get_all('collected')))
    
    df = clean_dataset(df)
    
    columns = ['id', 'title', 'body', 'issue_comments', 'html_url']
    df = df.filter(items=columns)
    
    mongo.save('issues', df)
    df.to_json(OUTPUT_FILE, orient='records')

# Clean data
def clean_dataset(dataset):
    cleaner = DataCleaner()
    fields = ['title', 'body']
   
    df = cleaner.clean(dataset, fields)
    df = remove_duplicates_no_comments(cleaner, df, fields)
    df = cleaner.filter_english(df, fields)
    
    return df

# Remove issues with duplicate title, body and no comments
def remove_duplicates_no_comments(cleaner, data, fields, 
                                  duplicate_each=False):
    comments = data[data['comments'] > 0]
    no_comments = data[data['comments'] == 0]
    
    no_comments = cleaner.remove_duplicates(no_comments, fields, 
                                            duplicate_each=duplicate_each)
    
    data = pd.concat([comments, no_comments])
    
    return data

# Run application        
if __name__ == '__main__':
    process_data()