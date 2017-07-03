import random
import itertools
import urllib.parse as urlparse

class GitHubIssueCollector:
    
    def __init__(self, req, mongo, info=None):
        self.req = req
        self.mongo = mongo
        self.issues = self.mongo.db.collected
        self.calls_left = dict()
        
        if info is None:
            self.info = {
                'repos_page': 1,
                'repo_name': '',
                'issues_page': 1,
                'comments_page': 1,
                'repo_sample': list(),
                'current_index': 0,
                'issue_number': 0,
                'total_issues': 0,
                'collect_total': 0,
                'collected_items': 0,
                'interrupted': False
            }
        else:
            self.info = info
    
    # Collect issues from repos
    def collect(self, page=1, sample_percent=25):
        if self.rate_limit('search') > 0:
            self.info['repos_page'] = page
            print('Fetching repos...')
            print('Traversing page %d of repos.' % page)
            
            res = self.get_repos(page)
            next_page = res['next_page']
            repos = res['data']['items']
            self.set_rate_limit(res['calls'], 'search')
            
            for repo in repos:
                repo_name = repo['full_name']
                
                if self.info['interrupted'] is True:
                    if repo_name != self.info['repo_name']:
                        continue
                    else:
                        self.info['interrupted'] = False
                        self.info['repo_sample'] = set(self.info['repo_sample'])
                        self.get_issues(repo_name, self.info['issues_page'])
                else: 
                    self.info['repo_name'] = repo_name
                    print('Fetching issues from %s' % repo_name)
                    
                    num_results = self.result_count(repo_name)
                    
                    if num_results is 0:
                        continue
                    else:
                        self.info['total_issues'] = num_results
                        self.info['collect_total'] = self.calc_total(sample_percent, self.info['total_issues'])
                        self.info['repo_sample'] = set(random.sample(range(0, self.info['total_issues'] - 1), self.info['collect_total']))
                        self.info['current_index'] = 0
                        self.info['collected_items'] = 0
                             
                        self.get_issues(repo_name)
            
            if next_page is not None:
                self.collect(next_page, sample_percent)
        else:
            self.req.wait()
            self.collect(page, sample_percent)
    
    # Collect a random sample of issues from random repos
    def collect_random(self, num_repos=30, num_issues=1, stars='5000..10000'):
         if self.rate_limit('search') > 0:
            print('Fetching repos...')
            res = self.get_repos(1, stars)
            num_results = int(res['data']['total_count'])
            next_page = res['next_page']
            
            sample = set(random.sample(range(num_results), num_repos))
            
            options = {
                'current_index': 0,
                'page': 1,
                'next_page': next_page, 
                'stars': stars,
                'items': res['data']['items']
            }
            
            repos = self.get_random_repos(sample, options)
            issues = list()
            
            for repo in repos:
                print('Getting issues from %s' % repo)
                count = self.result_count(repo)
                
                if count == 0:
                    continue
                
                sample_size = num_issues if num_issues < count else count
                sample = set(random.sample(range(count), sample_size))

                options = {
                    'current_index':0,
                    'page':1
                }
                
                issues.append(self.get_random_issues(repo, sample, options, issues=list()))
                
            return list(itertools.chain.from_iterable(issues))
         else:
            self.req.wait()
            self.collect_random(num_repos, num_issues, stars)
        
    # Get random repos
    def get_random_repos(self, sample, options, repos=list()):
        if options['items'] is not None:
            print('Traversing page %d of repos.' % (options['page']))
            
            for repo in options['items']:
                if options['current_index'] in sample:
                    repos.append(repo['full_name'])
                
                options['current_index'] += 1
                
            options['items'] = None
        else:
            if self.rate_limit('search') > 0:
                res = self.get_repos(options['next_page'], options['stars'])
                options['next_page'] = res['next_page']
                options['items'] = res['data']['items']
                
                self.get_random_repos(sample, options, repos)
            else:
                self.req.wait()
                self.get_random_repos(sample, options, repos)
        
        if len(repos) == len(sample):
            return repos
            
        if options['next_page'] is not None:
            options['page'] += 1
            return self.get_random_repos(sample, options, repos)
    
    # Get random issues
    def get_random_issues(self, repo, sample, options, issues): 
        print('Traversing page %d of issues.' % options['page'])
        
        params = {
            'state': 'closed',
            'sort': 'created',
            'direction': 'desc',
            'since': '2015-01-01T00:00:00Z',
            'per_page': 100,
            'page': options['page']
        }
        
        if self.rate_limit() > 0:
            url = self.req.build('repos/' + repo + '/issues', params)
            res = self.req.send(url)
            options['page'] = res['next_page']
            data = res['data']
            self.set_rate_limit(res['calls'])
            
            for issue in data:
                if 'pull_request' not in issue:
                    if options['current_index'] in sample:
                        issues.append(issue)
                        print('Issue collected.')
                        
                        if len(issues) == len(sample):
                            print('Exiting...')
                            return issues            
                    
                    options['current_index'] += 1
        
            if options['page'] is not None:
                return self.get_random_issues(repo, sample, options, issues)
        else:
            self.req.wait()
            self.get_random_issues(repo, sample, options, issues)
        
    # Fetch repositories
    def get_repos(self, page, stars='>=10000'):
        params = {
            'q': 'language:javascript stars:%s' % stars,
            'sort': 'stars',
            'order': 'desc',
            'per_page': 100,
            'page': page
        }
        
        url = self.req.build('search/repositories', params)
        
        return self.req.send(url)
    
    # Fetch issues from repo
    def get_issues(self, repo, page=1):
        if self.rate_limit() > 0:
            self.info['issues_page'] = page
            print('Traversing page %d of issues.' % page)
            print('Collected issues from %s: %d' % (repo, self.info['collected_items']))
            
            params = {
                'state': 'closed',
                'sort': 'created',
                'direction': 'desc',
                'since': '2015-01-01T00:00:00Z',
                'per_page': 100,
                'page': page
            }
            
            url = self.req.build('repos/' + repo + '/issues', params)
            res = self.req.send(url)
            next_page = res['next_page']
            data = res['data']
            self.set_rate_limit(res['calls'])
            
            for issue in data:
                if 'pull_request' not in issue:
                    num = issue['number']
                    
                    if num > self.info['issue_number']:
                        continue
                    
                    self.info['issue_number'] = num
                    
                    if self.info['current_index'] in self.info['repo_sample']:
                        issue_comments = list()
                             
                        if issue['comments'] > 0:
                            print('Fetching comments for issue %d (%d)' % (self.info['current_index'], num))
                            self.get_comments(issue['comments_url'], issue_comments)
                        
                        issue['issue_comments'] = issue_comments
                        self.issues.insert_one(issue)
                        print('Issue %d collected.' % self.info['current_index'])
                        self.info['collected_items'] += 1
                               
                    self.info['current_index'] += 1
                    
                    # Exit method after gathering the specified total
                    if self.info['collected_items'] >= self.info['collect_total']: 
                        return
            
            if next_page is not None:
                self.get_issues(repo, next_page)
        else:
            self.req.wait()
            self.get_issues(repo, page)
    
    # Fetch issue comments
    def get_comments(self, comments_url, issue_comments, page=1):
        if self.rate_limit() > 0:
            self.info['comments_page'] = page
            print('Retrieving comments...')
            print('Traversing page %d of comments.' % page)
            
            params = {
                'per_page': 100,
                'page': page
            }
            
            url = comments_url + '?' + urlparse.urlencode(params)
            res = self.req.send(url)
            data = res['data']
            next_page = res['next_page']
            self.set_rate_limit(res['calls'])
            
            for comment in data:
                issue_comments.append(comment)
                
            if next_page is not None:
                self.get_comments(comments_url, issue_comments, next_page)
        else:
            self.req.wait()
            self.get_comments(comments_url, issue_comments, page)
    
    # Retrieve total result count from API
    def result_count(self, repo):
        if self.rate_limit('search') > 0:       
            params = {
                'q': 'type:issue state:closed created:>=2015-01-01T00:00:00Z repo:' + repo
            }
            
            url = self.req.build('search/issues', params)
            res = self.req.send(url)
            items = res['data']['items']
            self.set_rate_limit(res['calls'], 'search')
            
            if items:
                self.info['issue_number'] = items[0]['number']
            
            return int(res['data']['total_count'])
        else:
            self.req.wait()
            self.result_count(repo)
    
    # Calculate how many issues are to be extracted
    def calc_total(self, percent, total):
        return round((percent / 100) * total)
    
    # Check current API rate limits
    def rate_limit(self, api_type='core'):        
        if api_type not in self.calls_left or self.calls_left[api_type] is 0:
            print('Getting rate limit from API')
            url = self.req.build('rate_limit')
            res = self.req.send(url)['data']['resources']
            
            remaining = res[api_type]['remaining']
        else:
            print('Getting rate limit from response')
            remaining = int(self.calls_left[api_type])
            
        print('API calls remaining: %d' % remaining)
        
        return remaining
    
    # Set API call count
    def set_rate_limit(self, value, api_type='core'):
        self.calls_left[api_type] = value