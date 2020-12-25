# coding: utf-8


import engine
import xbmc, xbmcgui, xbmcplugin, time, sys

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
    if isinstance(s, BaseException):
        import sys
        exc_type, exc_val, exc_tb = sys.exc_info()
        import traceback
        lines = traceback.format_exception(exc_type, exc_val, exc_tb, limit=10)
        for line in lines:
            xbmc.log (u'Torrserver: {0}'.format(line).encode('utf8'))
    else:
        xbmc.log (u'Torrserver: {0}'.format(s).encode('utf8'))


class Player(xbmc.Player):

    def __init__(self, uri=None, path=None, data=None, index=None, sort_index=None, name=None):
        #import vsdbg; vsdbg._bp()

        try:
            xbmc.Player.__init__(self)
            self.show_overlay = False

            self.fs_video = xbmcgui.Window(12005)

            x = 20
            y = 180
            w = self.fs_video.getWidth()
            h = 100

            self.info_label = xbmcgui.ControlLabel(x, y, w, h, '', textColor='0xFF00EE00', font='font16')
            self.info_label_bg = xbmcgui.ControlLabel(x+2, y+2, w, h, '', textColor='0xAA000000', font='font16')

            from settings import Settings
            s = Settings()

            self.engine = engine.Engine(uri=uri, path=path, data=data, log=_log, host=s.host, port=s.port)

            if not self.engine.success:
                dialog = xbmcgui.Dialog()
                dialog.notification('TorrServer', 'Server not started. Please start server or reconfigure settings',
                                    xbmcgui.NOTIFICATION_INFO, 5000)
                return

            ts = self.engine.torrent_stat()
            if len(ts['Files']) == 1:
                sort_index = 0
                index = 0
            else:
                if sort_index is None:
                    if name is not None:
                        sort_index = self.engine.get_ts_index(name)
                    elif index is not None:
                        sort_index = self.engine.id_to_files_index(index)

            self.file_id = sort_index
            self.engine.start(sort_index)

            if self.prebuffer():
                _log('Prebuffer success')

                playable_url = self.engine.play_url(sort_index)
                handle = int(sys.argv[1])
                list_item = xbmcgui.ListItem(path=playable_url)

                xbmcplugin.setResolvedUrl(handle, True, list_item)

                self.loop()

            if not s.save_in_database:
                _log("Remove from DB")
                self.engine.rem()

        except BaseException as e:
            _log('************************ ERROR ***********************')
            _log(e)

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
            line2 = u'S:{0} A:{1} T:{2}'.format(st['ConnectedSeeders'], st['ActivePeers'], st['TotalPeers'])
            line3 = u"D: {0}/сек [{1}/{2}]".format(downSpeed, humanizeSize(preloadedBytes), humanizeSize(preloadSize))
            if preloadSize > 0 and preloadedBytes > 0:
                prc = preloadedBytes * 100 / preloadSize
                if prc > 100:
                    prc = 100
                pDialog.update(prc, line2, line3)

                if preloadedBytes >= preloadSize:
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
            try:
                size		= int(info['FileStats'][self.file_id]['Length'])
                downloaded	= int(info['LoadedSize'])
                dl_speed	= int(info['DownloadSpeed'])
                percent = float(downloaded) * 100 / size
                if percent >= 0:
                    heading = u"{0} МB из {1} МB - {2}".format(downloaded/1024/1024, size/1024/1024, int(percent)) + r'%' + '\n'
                    if percent < 100:
                        heading += u"Скорость загрузки: {0} KB/сек\n".format(dl_speed/1024)
                        heading += u"Сиды: {0}    Пиры: {1}".format(info['ConnectedSeeders'], info['ActivePeers'])

                    self.info_label.setLabel(heading)
                    self.info_label_bg.setLabel(heading)
            except BaseException as e:
                _log('************************ ERROR ***********************')
                _log(e)
                
    def loop(self):
        while not xbmc.abortRequested and not self.isPlaying():
            xbmc.sleep(100)

        _log('************************ START Playing ***********************')
            
        while not xbmc.abortRequested and self.isPlaying():
            xbmc.sleep(1000)
            self.UpdateProgress()

        _log('************************ FINISH Playing ***********************')
            
    def __del__(self):				self._hide_progress()
    def onPlayBackPaused(self):		self._show_progress()
    def onPlayBackResumed(self):	self._hide_progress()
    def onPlayBackEnded(self):		self._hide_progress()
    def onPlayBackStopped(self):	self._hide_progress()
    
    
