# coding: utf-8

import requests
import json
import time

def no_log(s):
	pass

def url2path(url):
	import urllib
	from urlparse import urlparse
	return urllib.url2pathname(urlparse(url).path)

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

	def echo(self):
		url = self.make_url('/echo')
		try:
			r = requests.get(url)
		except requests.ConnectionError as e:
			self.log(unicode(e))
			return False

		if r.status_code == requests.codes.ok:
			self.log(r.text)
			return True

		try:
			r.raise_for_status()
		except requests.HTTPError as e:
			self.log(unicode(e))
		except:
			pass

		return False

	def stat(self):
		return self.request('stat', data={'Hash': self.hash}).json()
		
	def list(self):
		return self.request('list').json()

	def rem(self):
		self.request('rem', data={'Hash': self.hash})

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
	def _wait_for_data(self, timeout=10):
		self.log('_wait_for_data')
		files = self.list()
		for n in range(timeout*2):
			st = self.stat()
			try:
				self.log(st['TorrentStatusString'])

				if st['TorrentStatusString'] != 'Torrent working':
					time.sleep(0.5)
				else:
					break
			except KeyError:
				self.log('"TorrentStatusString" not in stat')
				time.sleep(0.5)

	def __init__(self, uri=None, path=None, data=None, host='127.0.0.1', port=8090, log=no_log):
		self.uri = uri
		self.host = host
		self.port = port
		self.hash = None
		self.log = log
		self.success = True

		if not self.echo():
			self.success = False
			return

		if uri:
			if uri.startswith('magnet:') or uri.startswith('http:') or uri.startswith('https:'):
				self.add(uri)
				self._wait_for_data()
				return

			if uri.startswith('file:'):
				path = url2path(uri)

		if path and not data:
			with open(path, 'rb') as f:
				data = f.read()

		if data:
			name = path or 'Torrserver engine'
			self.upload(name, data)
			self._wait_for_data()

	def start_preload(self, url):
		def download_stream():
			req = requests.get(url, stream=True)
			for chunk in req.iter_content(chunk_size=128):
				self.log('dowload chunk: 128')

		import threading
		t = threading.Thread(target=download_stream)
		t.start()

	def id_to_files_index(self, file_id):
		st = self.stat()
		ts = self.torrent_stat()
		index = 0
		for item in st.get('FileStats') or []:
			if item['Id'] == file_id:
				self.log(unicode(item['Path']))

				files_index = 0
				for fl in ts['Files']:
					self.log(unicode(fl['Name']))
					if item['Path'] == fl['Name']:
						return files_index
					files_index += 1

				files_index = 0
				for fl in ts['Files']:
					if item['Lenght'] == fl['Size']:
						return files_index
					files_index += 1

			index += 1

		self.log('Index not found, just return file_id')
		return file_id

	def start(self, start_index=None):
		self.log('Engine start')

		for n in range(5):
			self.log('Try # {0}'.format(n))
			try:
				files = self.list()
				self.log(unicode(files))

				if start_index is None:
					start_index = 0

				start_index = self.id_to_files_index(start_index)

				for torrent in files:
					if self.hash == torrent['Hash']:
						file = torrent['Files'][start_index]
						preload = file['Preload']

						self.start_preload(self.make_url(preload))
						return
				break
			except BaseException as e:
				self.log(e)
				time.sleep(0.5)
				continue

		self.log('Preload not started')

	def torrent_stat(self):
		lst = self.list()

		for torr in lst:
			if self.hash == torr['Hash']:
				return torr

	def file_stat(self, index):
		ts = self.torrent_stat()
		index = self.id_to_files_index(index)
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

if __name__ == '__main__':
	path = 'D:\\book7.torrent'
	file_id = 2

	def log(s):
		with open('engine.log', 'a') as f:
			try:
				f.write(s.encode('utf-8'))
			except:
				f.write(s)
			f.write('\n')

	e = Engine(path=path, host='192.168.1.5', log=log)

	play_url = e.play_url(file_id)

	print(play_url)

	

