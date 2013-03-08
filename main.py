import json, os.path
from reddit import Reddit, RedditException

class Cliddit(object):
	def __init__(self):
		self.reddit = Reddit()

		try:
			self.config = json.load(file(os.path.expanduser('~/.cliddit'), 'r'))
		except:
			self.config = {}

		if 'user' in self.config:
			self.reddit.login(*self.config['user'])

	def save_config(self):
		with file(os.path.expanduser('~/.cliddit'), 'w') as fp:
			json.dump(self.config, fp)

	def login(self, username, password):
		if self.reddit.login(username, password):
			self.username = self.reddit.username
			self.config['user'] = username, password
			self.save_config()
			return True
		else:
			return False

if __name__=='__main__':
	Cliddit()
