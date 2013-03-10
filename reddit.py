from requests import Session
import json
from pprint import pprint

class RedditException(Exception):
	pass

class Reddit(object):
	def __init__(self):
		self.init_session()

	def init_session(self):
		self.session = Session()
		self.session.headers['user-agent'] = 'Cliddit v0.0.1'
		self.modhash = None

	def get(self, path, **kwargs):
		req = self.session.get('http://reddit.com/' + path, params=kwargs)
		if req.status_code == 200:
			return req.json()
		else:
			return False

	def post(self, path, **kwargs):
		kwargs['api_type'] = 'json'
		if self.modhash:
			kwargs['uh'] = self.modhash
		req = self.session.post('http://www.reddit.com/' + path, data=kwargs)
		if req.status_code == 200:
			return req.json()
		else:
			return False

	def login(self, username, password):
		req = self.post('api/login', user=username, passwd=password)['json']
		if req['errors']:
			raise RedditException(req['errors'][0][1])
		else:
			self.username = username
			return True

	def logout(self):
		self.init_session()

	def list_posts(self, subreddit=None):
		if subreddit:
			path = 'r/' + subreddit
		else:
			path = '/'
		entries = []
		top = self.get(path + '.json')
		for data in top['data']['children']:
			data = data['data']
			entries.append(dict(
				title=data['title'], 
				user=data['author'], 
				score=data['score'], 
				selftext=data['selftext'] if data['is_self'] else None, 
				comments=data['num_comments'], 
				post=(data['subreddit'], data['id'])
			))

		if subreddit:
			info = self.get(path + '/about.json')['data']
			name, title = info['display_name'], info['title']
		else:
			name, title = 'home', 'Reddit Home'

		return name, title, entries

	def get_post(self, id):
		def parse_comments(comments):
			_children = comments['data']['children']
			children = []
			for data in _children:
				data = data['data']
				children.append(dict(
					user=data['author'], 
					body=data['body'], 
					score=data['ups']-data['downs'], 
					votes=(data['ups'], data['downs']), 
					comments=parse_comments(data['replies']) if data['replies'] else []
				))
			return children

		post = self.get('r/%s/comments/%s.json' % id)
		info, comments = post
		info = info['data']['children'][0]['data']

		return dict(
			subreddit=info['subreddit'], 
			user=info['author'], 
			score=info['score'], 
			votes=(info['ups'], info['downs']), 
			title=info['title'], 
			selftext=info['selftext'] if info['is_self'] else None, 
			link=info['url'] if not info['is_self'] else None, 
			comments=parse_comments(comments)
		)

if __name__=='__main__':
	reddit = Reddit()
	pprint(reddit.get_post((u'r4r', u'19yfmk')))
	pprint(reddit.get_post((u'r4r', u'19ym56')))
