import os
import json
from githubanalyzer.collector import GitHubIssueCollector
from githubanalyzer.mongodb import MongoDB
from githubanalyzer.apirequest import APIRequest

# Constants
FILE_PATH = '../data/'
ACCESS_TOKEN = 'YOUR_GITHUB_ACCESS_TOKEN'
API_ENDPOINT = 'https://api.github.com/'
USER_AGENT = 'CUSTOM_USER_AGENT'
OUTPUT_FILE = FILE_PATH + 'issues.json'
INFO_FILE = FILE_PATH + 'info.json'
HTTP_HEADERS = {
    'User-Agent': USER_AGENT, 
    'Authorization': 'token ' + ACCESS_TOKEN,
    'Accept': 'application/vnd.github.squirrel-girl-preview'
}

# Initialize script
def init():
    req = APIRequest(API_ENDPOINT, HTTP_HEADERS)
    mongo = MongoDB('github')

    if len(get_collected(mongo)) > 0:
        collector = GitHubIssueCollector(req, mongo, get_info())        
    else:
        collector = GitHubIssueCollector(req, mongo)
        
    collect_data(collector)
    
# Get collection info
def get_info():
    if os.stat(INFO_FILE).st_size != 0:
        with open(INFO_FILE, 'r') as f:
            return json.load(f)
    
    return None

# Get all collected issues
def get_collected(mongo):    
    return list(mongo.get_all('collected'))
    
# Save collection progress
def save_progress(collector):
    collector.info['interrupted'] = True
    collector.info['repo_sample'] = list(collector.info['repo_sample'])
                  
    with open(INFO_FILE, 'w') as info:
        json.dump(collector.info, info)
            
# Perform data collection
def collect_data(collector, recur_level=1):
    try:
        collector.collect(page=collector.info['repos_page'])
    except MemoryError:
        print('Memory limit exceeded.')
    except Exception as e:
        print('Collection interrupted.')
        print(e.args)
        
        save_progress(collector)
        collect_data(collector, recur_level=recur_level+1)
    except:
         print('Manual interruption.')
    finally:
        if recur_level is 1:
            save_progress(collector)
            
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:    
                json.dump(get_collected(), f)
            
            print('Collection complete.')
    
# Run application
if __name__ == '__main__':
    init()