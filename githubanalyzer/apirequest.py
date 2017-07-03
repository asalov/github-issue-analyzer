import time
import json
import urllib.request as urlreq
import urllib.parse as urlparse

class APIRequest:
    
    def __init__(self, endpoint, headers):
        self.endpoint = endpoint
        self.headers = headers
    
    # Build full URL path to API endpoint
    def build(self, path, params=None):
        url = self.endpoint + path
        
        if params is not None:
            url += '?' + urlparse.urlencode(params)
            
        return url
    
    # Send HTTP request
    def send(self, url, method='GET', timeout=10):        
        req = urlreq.Request(url, headers=self.headers, method=method)
        
        try:
            res = urlreq.urlopen(req, timeout=timeout)
            
            headers = res.info()
        
            link_header = headers.__getitem__('Link')
            data = json.loads(bytes.decode(res.read()))    
            page = None
        
            if link_header is not None:
                page = self.get_next_page(link_header)
        
            return { 
                'data': data, 
                'next_page': page,
                'calls': headers.__getitem__('X-RateLimit-Remaining')
            }
        except Exception as e:
            print('URL request error.')
            print(e.args)
            self.wait()
            self.send(url, method, timeout)
    
    # Parse Link header to get index of next page
    def get_next_page(self, link_header):
        headers = link_header.split(',')
        headers = [header.split(';') for header in headers]
    
        for header in headers:
            if header[1].find('next') > -1:
                query_str = urlparse.urlsplit(header[0]).query[:-1]
            
                kvp = dict(urlparse.parse_qsl(query_str)) 
            
                return int(kvp['page'])
        
        return None
    
    # Delay script execution
    def wait(self):
        print('Waiting...')
        time.sleep(30)