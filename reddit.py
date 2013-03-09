from requests import Session
import json

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

	def list_posts(self, subreddit):
		if subreddit:
			path = 'r/' + subreddit
		else:
			path = '/'
		entries = []
		for data in self.get(path + '.json')['data']['children']:
			data = data['data']
			entries.append(dict(
				title=data['title'], 
				user=data['author'], 
				score=data['score'], 
				selftext=data['selftext'] if data['is_self'] else None, 
				comments=data['num_comments'], 
				post=(data['subreddit'], data['id'])
			))
		return entries