# coding: utf-8

import requests
import json
import time

def no_log(s):
	pass

class BaseEngine(object):

	def make_url(self, path):
		return 'http://' + self.host + ':' + str(self.port) + path

	def request(self, name, method='POST', data=None, files=None):
		url = self.make_url('/torrent/' + name)
		
		self.log(unicode(url))
		
		if data:
			data = json.dumps(data)
		
		r = requests.post(url, data=data, files=files)
		return r

	def stat(self):
		return self.request('stat', data={'Hash': self.hash}).json()
		
	def list(self):
		return self.request('list').json()

	def drop(self):
		self.request('drop', data={'Hash': self.hash})
		
	def upload_file(self, filename):
		files = {'file': open(filename, 'rb')}
		return self.request('upload', files=files)
		
	def add(self, uri):
		r = self.request('add', data={'Link': uri, "DontSave": False})
		self.hash = r.content
		
		self.log('Engine add')
		self.log(self.hash)
		self.log(unicode(r.headers))
		self.log(r.text)
		
		return r.status_code == requests.codes.ok

	def upload(self, name, data):
		files = {'file': (name, data)}

		r = self.request('upload', files=files)
		self.hash = r.json()[0]

		self.log('Engine upload')
		self.log(self.hash)
		self.log(unicode(r.headers))
		self.log(r.text)

		return r.status_code == requests.codes.ok


class Engine(BaseEngine):
	def __init__(self, uri=None, path=None, data=None, host='127.0.0.1', port=8090, log=no_log):
		self.uri = uri
		self.host = host
		self.port = port
		self.hash = None
		self.log = log
		
		if uri:
			if uri.startswith('magnet:') or uri.startswith('http:') or uri.startswith('https:'):
				self.add(uri)
				return

		if path:
			with open(path, 'rb') as f:
				data = f.read()

		if data:
			name = path or 'Torrserver engine'
			self.upload(name, data)

	def start_preload(self, url):
		def download_stream():
			req = requests.get(url, stream=True)
			for chunk in req.iter_content(chunk_size=128):
				self.log('dowload chunk: 128')

		import threading
		t = threading.Thread(target=download_stream)
		t.start()

	def start(self, start_index=None):

		for n in range(5):
			try:
				files = self.list()
		
				self.log(unicode(files))

				if start_index is None:
					start_index = 0
		
				for torrent in files:
					if self.hash == torrent['Hash']:
						file = torrent['Files'][start_index]
						preload = file['Preload']

						self.start_preload(self.make_url(preload))
						return
				break
			except:
				time.sleep(0.5)
				continue

	def torrent_stat(self):
		lst = self.list()
		
		for torr in lst:
			if self.hash == torr['Hash']:
				return torr

	def file_stat(self, index):
		ts = self.torrent_stat()
		return ts['Files'][index]

	def play_url(self, index):
		fs = self.file_stat(index)
		return self.make_url(fs['Link'])

	def progress(self):
		info = self.stat()
		percent = float(info['downloaded']) * 100 / info['size'];

	def buffer_progress(self):
		st = self.stat()

		self.log(unicode(st))

		preloadedBytes = st.get('PreloadedBytes', 0)
		preloadSize = st.get('PreloadSize', 0)
		if preloadSize > 0 and preloadedBytes > 0:
			prc = preloadedBytes * 100 / preloadSize
			if prc >= 100:
				prc = 100
			return prc

		return 0

