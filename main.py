import json, os.path, sys
from reddit import Reddit, RedditException
from urwid import *

class Dialog(object):
	def __init__(self, cld, contents, title):
		self.cld = cld
		self.bottom = cld.frame.contents['body'][0]
		self.top = LineBox(contents, title)
		self.set_title = self.top.set_title

		overlay = Overlay(self.top, self.bottom, 'center', ('relative', 50), 'middle', 'pack')

		cld.frame.contents['body'] = overlay, None

	def close(self):
		self.cld.frame.contents['body'] = self.bottom, None

def button(text):
	def sub(func):
		return Button(text, on_press=lambda _: func())
	return sub

keymap = {}
class Cliddit(object):
	palette = [
		('status', 'white', 'dark blue'), 
		('status_sep', 'light blue', 'dark blue'), 
		('body', 'light gray', 'black')
	]

	def key(val):
		def sub(func):
			keymap[val] = func
			return func
		return sub

	def __init__(self, *args):
		self.reddit = Reddit()
		self.username = None

		loop = MainLoop(self.build_gui(), self.palette, unhandled_input=self.unhandled)

		try:
			self.config = json.load(file(os.path.expanduser('~/.cliddit'), 'r'))
		except:
			self.config = {}
		if 'user' in self.config:
			self.login(*self.config['user'])

		try:
			loop.run()
		except KeyboardInterrupt:
			return

	def save_config(self):
		with file(os.path.expanduser('~/.cliddit'), 'w') as fp:
			json.dump(self.config, fp)

	def login(self, username, password):
		try:
			self.reddit.login(username, password)
			self.username = self.reddit.username
			self.config['user'] = username, password
			self.save_config()

			self.build_header()
			self.build_footer()
			return True
		except RedditException, e:
			return str(e)

	def logout(self):
		self.username = None
		if 'user' in self.config:
			del self.config['user']
			self.save_config()
		self.build_header()
		self.build_footer()

	def unhandled(self, key):
		if key in keymap:
			keymap[key](self)

	def dialog(self, widget, title=''):
		return Dialog(self, widget, title)

	@key('q')
	def _quit(self):
		raise ExitMainLoop()

	@key('?')
	def _help(self):
		pass

	@key('l')
	def _login(self):
		if self.username:
			self.show_logout()
		else:
			self.show_login()

	def show_login(self):
		@button('Login')
		def login():
			err = self.login(username.edit_text, password.edit_text)
			if err == True:
				dialog.close()
			else:
				dialog.set_title(err)
				username.set_edit_text('')
				password.set_edit_text('')
				nbody.focus_position = 0
		cancel = Button('Cancel', lambda _: dialog.close())

		username = Edit('Username: ')
		password = Edit('Password: ', mask='#')

		nbody = Pile([
			username, password, 
			Columns([login, cancel])
		])

		dialog = self.dialog(nbody, 'Login')

	def show_logout(self):
		confirmation = Text('Are you sure you want to logout?')

		@button('Yes')
		def yes():
			self.logout()
			dialog.close()

		no = Button('No', lambda _: dialog.close())

		nbody = Pile([
			confirmation,
			Columns([yes, no])
		])

		dialog = self.dialog(nbody, 'Logout')

	def build_gui(self):
		body = Filler(Text('Hello World!'))
		
		self.frame = Frame(body)
		self.build_header()
		self.build_footer()

		return self.frame

	def build_header(self):
		self.header = AttrMap(
			Columns([
				Text('Cliddit v0.0.1'), 
				Text(self.username if self.username else 'Not logged in', align='right')
			]), 
			'status'
		)
		self.frame.contents['header'] = self.header, None

	def build_footer(self):
		self.footer = AttrMap(Columns([Text('Footer'), Text('foo', align='right')]), 'status_sep')

		self.frame.contents['footer'] = self.footer, None

if __name__=='__main__':
	Cliddit(*sys.argv[1:])
