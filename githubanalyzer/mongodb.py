from pymongo import MongoClient
import numpy as np

class MongoDB:
    
    def __init__(self, db, host='localhost', port=27017, credentials={}):
        self.client = MongoClient(host, port)
        self.db = self.client[db]
        
        if credentials:
            self.client[db].authenticate(credentials['user'], credentials['password'])
    
    # Get all items in collection
    def get_all(self, collection, fields={'_id':0}):
        col = self.db[collection]
        
        return col.find({}, fields)
    
    # Get number of clusters
    def cluster_count(self):
        col = self.db.clusters
        
        return len(col.distinct('cluster_index'))
        
    # Get issues in cluster
    def get_cluster(self, index):
        col = self.db.clusters
        
        return col.find({'cluster_index': index}, {'_id':0, 'cluster_index':0})
    
    # Get issues in id list
    def get_issues_in_list(self, issue_list, fields, column='id'):
        col = self.db.issues
        
        return col.find({column: { '$in': issue_list}}, fields)
    
    # Assign cluster index to issues
    def assign_clusters(self, labels):
        col = self.db.clusters
        
        res = col.find()
        
        for index, cluster in enumerate(res):
            col.update({'id': cluster['id']}, { '$set': {'cluster_index': int(labels[index])}})
            
    # Save dataframe to collection
    def save(self, collection, data, needs_conversion=False):            
        col = self.db[collection]
        entries = data.to_dict(orient='records')
        
        if needs_conversion is True:
            for row in entries:
                for ind, val in row.items():
                    if isinstance(val, np.int64):
                        row[ind] = int(val)
            
        col.insert_many(entries)