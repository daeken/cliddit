#!/usr/bin/env python
# -*- coding: utf8 -*-

import json, os.path, sys, traceback
from functools import *
from reddit import Reddit, RedditException
from urwid import *

def partial_complete(func, *args, **kwargs):
	def sub(*_, **__):
		return func(*args, **kwargs)
	return sub

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

class Window(object):
	caption = 'unknown'
	title = 'Untitled'

	def view_post(self, post):
		pass

	def view_user(self, user):
		pass

class SubRedditWindow(Window):
	def __init__(self, top, subreddit=None):
		self.top = top
		self.caption, self.title, self.posts = self.top.reddit.list_posts(subreddit)

		contents = []
		for post in self.posts:
			contents.append(
				Columns([
					Text('%i points' % post['score']), 
					Button(('bold', post['title']), partial_complete(self.view_post, post['post'])), 
					Button(post['user'], partial_complete(self.view_user, post['user']))
				])
			)

		walker = SimpleFocusListWalker(contents)
		self.widget = ListBox(walker)

def button(text):
	def sub(func):
		return Button(text, on_press=lambda _: func())
	return sub

keymap = {}
keyeat = 'up down left right'.split(' ')
class Cliddit(object):
	palette = [
		('status', 'white', 'dark blue'), 
		('status_sep', 'light blue', 'dark blue'), 
		('body', 'light gray', 'black'), 
		('bold', 'white', 'black')
	]

	def key(val):
		def sub(func):
			keymap[val] = func
			return func
		return sub

	def __init__(self, *args):
		self.reddit = Reddit()
		self.username = None

		self.windows = []

		loop = MainLoop(self.build_gui(), self.palette, unhandled_input=self.unhandled)

		try:
			self.config = json.load(file(os.path.expanduser('~/.cliddit'), 'r'))
		except:
			self.config = {}
		if 'user' in self.config:
			self.login(*self.config['user'])

		self.add_window(SubRedditWindow(self))

		self.last_tb = None
		while True:
			try:
				loop.run()
				break
			except KeyboardInterrupt:
				return
			except:
				self.show_error()

		if self.last_tb:
			print >>sys.stderr, self.last_tb

	def show_error(self):
		self.last_tb = traceback.format_exc()
		err = '\n'.join(self.last_tb.split('\n')[-4:-1])
		@button('Exit')
		def exit():
			raise ExitMainLoop()
		@button('Close')
		def close():
			dialog.close()
			self.last_tb = None

		dialog = self.dialog(
			Pile([
				Text(err), 
				Columns([close, exit])
			]), u'¡Exception!'
		)
	
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
		if key in keyeat:
			pass
		elif key in keymap:
			keymap[key](self)
		elif isinstance(key, str) and key.startswith('meta '):
			self.meta(key[5:])
		elif isinstance(key, tuple):
			pass
		else:
			self.alert('Unhandled key: %r' % (key, ))

	def meta(self, key):
		keys = '1234567890qwertyuiopasdfghjkl;zxcvbnm,./'
		if key not in keys:
			return
		id = keys.index(key)
		self.set_current_window(id)

	def dialog(self, widget, title=''):
		return Dialog(self, widget, title)

	def alert(self, notice):
		dialog = self.dialog(
			Pile([
				Text(notice), 
				Button('Close', lambda _: dialog.close())
			]), 'Alert'
		)

	@key('q')
	def _quit(self):
		raise ExitMainLoop()

	@key('ctrl w')
	def _closewindow(self):
		self.close_window()

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
		self.frame = Frame(Filler(None))
		self.build_header()
		self.build_footer()

		return self.frame

	def build_header(self):
		self.header = AttrMap(
			Columns([
				Text(u'Cliddit v0.0.1 -- %s' % self.get_current_window().title if self.get_current_window() else 'Cliddit v0.0.1'), 
				Text(self.username if self.username else 'Not logged in', align='right')
			]), 
			'status'
		)
		self.frame.contents['header'] = self.header, None

	def build_footer(self):
		self.footer = AttrMap(Columns([Text('Footer'), Text('foo', align='right')]), 'status_sep')

		self.frame.contents['footer'] = self.footer, None

	def add_window(self, window):
		self.windows.append(window)
		self.set_current_window(len(self.windows) - 1)

	def close_window(self):
		if len(self.windows) > 1:
			del self.windows[self.current_window]
			if self.current_window:
				self.current_window -= 1
			self.set_current_window(self.current_window)

	def get_current_window(self):
		if self.windows:
			return self.windows[self.current_window]
		else:
			return None

	def set_current_window(self, i):
		if i >= len(self.windows):
			return
		self.current_window = i
		self.frame.contents['body'] = self.windows[self.current_window].widget, None
		self.build_header()
		self.build_footer()

if __name__=='__main__':
	Cliddit(*sys.argv[1:])
