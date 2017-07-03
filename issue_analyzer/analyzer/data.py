from sklearn.externals import joblib
from githubanalyzer.mongodb import MongoDB
from githubanalyzer.solutionfinder import SolutionFinder

FILE_PATH = '../../data/'
CLUSTERING_MODEL_FILE = FILE_PATH + 'clustering_model.pkl'

class IssueAnalyzer:

	def __init__(self):
		self.clusterer = joblib.load(CLUSTERING_MODEL_FILE)
		self.db = MongoDB('github')
		self.finder = SolutionFinder(self.clusterer, self.db)

	# Transform issue into vector
	def transform(self, text):
		vector = self.finder.vectorize_data(text)

		if vector is None:
			return vector

		return self.clusterer.scale_func.transform(vector)

	# Assign vector to cluster
	def assign(self, vector, level=3):
		self.vector = vector
		self.level = level
		cluster_assignments = self.clusterer.predict(self.vector, level=self.level)
		self.all_issues = list(self.db.get_all('clusters'))

		cluster_features = self.get_features(cluster_assignments[0])
		self.features = [item[1] for item in cluster_features]
		indices = [item[0] for item in cluster_features]
		self.cluster_issues = [item for ind, item in enumerate(self.all_issues) if ind in indices]

	# Get top rated comments
	def get_comments(self):
		options = self.search_options(self.level)
		similar = self.finder.find_similar(self.vector, self.features, self.cluster_issues, 
											max_results=options['max_results'], max_dist=options['max_dist'])

		self.comment_results = list()
		
		if not similar:
			return list()

		comments = self.finder.get_top_comments(similar)

		for comm in comments:
			comm_url = comm['html_url']
			pos = comm_url.rfind('#')
			self.comment_results.append(comm_url[:pos])

		return comments

	# Find most similar issues
	def similar_issues(self):
		if self.comment_results:
			res = list(self.db.get_issues_in_list(self.comment_results, {'_id':0, 'id':1}, column='html_url'))
			ids = [item['id'] for item in res]
			indices = [ind for ind, item in enumerate(self.all_issues) if item['id'] in ids]
			features = [item for ind, item in enumerate(self.clusterer.scaled_features) if ind not in indices]
			issues = [item for ind, item in enumerate(self.all_issues) if ind not in indices]

			return self.finder.find_similar(self.vector, features, issues)

		return self.finder.find_similar(self.vector, self.clusterer.scaled_features, self.all_issues)

	# Get features in cluster
	def get_features(self, indices):
		if isinstance(indices, list):
			levels = len(indices)
			sublevel = self.clusterer.hierarchy[indices[0]]

			if levels == 2:
				if indices[1] in sublevel:
					return sublevel[indices[1]]['features']

				return self.get_cluster_features(sublevel['features'], sublevel['model'], indices[1])
			
			third_lvl = sublevel[indices[1]]
			return self.get_cluster_features(third_lvl['features'], third_lvl['model'], indices[2])
		
		return self.clusterer.hierarchy[indices]['features']

	# Get features based on cluster index
	def get_cluster_features(self, all_features, model, index):
		return [item for ind, item in enumerate(all_features) if model.labels_[ind] == index]

	# Get search options according to search level
	def search_options(self, search_level):
		return {
			1: {
				'max_results': 50,
				'max_dist': 1.25
			},
			2: {
				'max_results': 30,
				'max_dist': 0.95			
			},
			3: {
				'max_results': 15,
				'max_dist': 0.75
			}
		}.get(search_level)