from django.shortcuts import render
from django.http import JsonResponse
from .apps import AnalyzerConfig

import time

# Display start page
def index(request):
	res = dict()

	if request.method == 'GET' and 'q' in request.GET:
		req = request.GET
		res = search(req['q'], req['level'])

	return render(request, 'analyzer/index.html', res)

# Show results
def results(request):
	return JsonResponse(search(request.GET['q'], request.GET['level']))

# Search for solutions
def search(query, level):
	analyzer = AnalyzerConfig.analyzer

	start = time.clock()
	vector = analyzer.transform(query)
	print('Vector transformation: %f' % (time.clock() - start))

	lvl = int(level)

	res = {
		'q': query,
		'level': (4 - lvl),
		'results': dict(),
		'has_results': False,
		'search_made': True
	}

	if vector is not None:
		start = time.clock()
		analyzer.assign(vector, level=lvl)
		print('Assigning vector to cluster: %f' % (time.clock() - start))

		start = time.clock()
		res['results']['solutions'] = analyzer.get_comments()
		print('Getting comments: %f' % (time.clock() - start))

		start = time.clock()
		res['results']['similar'] = analyzer.similar_issues()
		print('Retrieving similar issues: %f' % (time.clock() - start))

		if len(res['results']['solutions']) > 0 or len(res['results']['similar']) > 0:
			res['has_results'] = True

	return res