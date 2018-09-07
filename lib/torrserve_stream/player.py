# coding: utf-8


import engine
import xbmc, xbmcgui, time

def humanizeSize(size):
	B = u"б"
	KB = u"Кб"
	MB = u"Мб"
	GB = u"Гб"
	TB = u"Тб"
	UNITS = [B, KB, MB, GB, TB]
	HUMANFMT = "%.2f %s"
	HUMANRADIX = 1024.

	for u in UNITS[:-1]:
		if size < HUMANRADIX : return HUMANFMT % (size, u)
		size /= HUMANRADIX

	return HUMANFMT % (size,  UNITS[-1])

def _log(s):
	xbmc.log (u'Torrserver: {}'.format(s))


class Player(xbmc.Player):

	def __init__(self, uri=None, path=None, data=None, index=None):
		index = index or 0;
		xbmc.Player.__init__(self)
		self.show_overlay = False

		self.fs_video = xbmcgui.Window(12005)

		x = 20
		y = 120
		w = self.fs_video.getWidth()
		h = 100

		self.info_label = xbmcgui.ControlLabel(x, y, w, h, '', textColor='0xFF00EE00', font='font16')
		self.info_label_bg = xbmcgui.ControlLabel(x+2, y+2, w, h, '', textColor='0xAA000000', font='font16')
		
		self.engine = engine.Engine(uri=uri, path=path, data=data, log=_log)
		
		s = self.engine.start(index)

		if self.prebuffer():
			_log('Prebuffer success')
			self.play(self.engine.play_url(index))
			self.loop()

	def prebuffer(self):
		pDialog = xbmcgui.DialogProgress()
		pDialog.create("TorrServer", "Wait for info....")
		success = False
		counter = 0
		while True:
			if counter > 60:
				return False

			if pDialog.iscanceled() :
				pDialog.close()
				self.engine.drop()
				break

			time.sleep(0.5)
			st = self.engine.stat()
			_log(st)

			if 'message' in st:
				counter += 1
				continue

			downSpeed = humanizeSize(st['DownloadSpeed'])
			preloadedBytes = st['PreloadedBytes']
			preloadSize = st['PreloadSize']
			line2 = u'S:{} A:{} T:{}'.format(st['ConnectedSeeders'], st['ActivePeers'], st['TotalPeers'])
			line3 = u"D: {0}/сек [{1}/{2}]".format(downSpeed, humanizeSize(preloadedBytes), humanizeSize(preloadSize))
			if preloadSize > 0 and preloadedBytes < preloadSize:
				prc = preloadedBytes * 100 / preloadSize
				if prc > 100:
					prc = 100
				pDialog.update(prc, line2, line3)
			elif preloadedBytes > preloadSize:
				success = True
				pDialog.close()
				break

		return success


	def _show_progress(self):
		if not self.show_overlay:
			self.fs_video.addControls([self.info_label_bg, self.info_label])
			self.show_overlay = True

	def _hide_progress(self):
		if self.show_overlay:
			self.fs_video.removeControls([self.info_label_bg, self.info_label])
			self.show_overlay = False

	def UpdateProgress(self):
		if self.show_overlay:
			info = self.engine.stat()
			percent = float(info['downloaded']) * 100 / info['size'];
			if percent >= 0:
				heading = u"{} МB из {} МB - {}".format(info['downloaded'], info['size'], int(percent)) + r'%' + '\n'
				if percent < 100:
					heading += u"Скорость загрузки: {} KB/сек\n".format(info['dl_speed'])
					heading += u"Сиды: {}    Пиры: {}".format(info['num_seeds'], info['num_peers'])

				self.info_label.setLabel(heading)
				self.info_label_bg.setLabel(heading)
				
	def loop(self):
		while not self.isPlaying():
			xbmc.sleep(100)
			
		while self.isPlaying():
				xbmc.sleep(1000)
				
			
	def __del__(self):				self._hide_progress()
	def onPlayBackPaused(self):		self._show_progress()
	def onPlayBackResumed(self):	self._hide_progress()
	def onPlayBackEnded(self):		self._hide_progress()
	def onPlayBackStopped(self):	self._hide_progress()
	
	
