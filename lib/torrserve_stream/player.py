# coding: utf-8

from __future__ import absolute_import
from typing import Any

from . import engine
from .overlay import Overlay, _humanizeSize
import xbmc, xbmcgui, xbmcplugin, time, sys

class OurDialogProgress(xbmcgui.DialogProgress):
    def create(self, heading, line1="", line2="", line3=""):
        try:
            xbmcgui.DialogProgress.create(self, heading, line1, line2, line3)   #type: ignore
        except TypeError:
            message = line1
            if line2:
                message += '\n' + line2
            if line3:
                message += '\n' + line3
            xbmcgui.DialogProgress.create(self, heading, message)

    def update(self, percent, line1="", line2="", line3=""):
        try:
            xbmcgui.DialogProgress.update(self, int(percent), line1, line2, line3)  #type: ignore
        except TypeError:
            message = line1
            if line2:
                message += '\n' + line2
            if line3:
                message += '\n' + line3
            xbmcgui.DialogProgress.update(self, int(percent), message)


def _log(s):
    import sys
    def make_message(_s):
        if sys.version_info < (3, 0):
            return u'Torrserver: {0}'.format(unicode(_s)).encode('utf8')
        else:
            return 'Torrserver: {0}'.format(str(_s))

    if isinstance(s, BaseException):
        exc_type, exc_val, exc_tb = sys.exc_info()
        import traceback
        lines = traceback.format_exception(exc_type, exc_val, exc_tb, limit=10)
        for line in lines:
            xbmc.log (make_message(line))
    else:
        xbmc.log (make_message(s))


class Player(xbmc.Player):

    def __init__(self, uri=None, path=None, data=None, index=None, sort_index=None, name=None, art=None, use_overlay=True):
        ''' sort_index: 0-based file index
            index:      0-based playable_items() index
        '''

        try:
            xbmc.Player.__init__(self)
            self._overlay = None

            from .settings import Settings
            s = Settings()

            self.engine = engine.Engine(uri=uri, path=path, data=data, log=_log, **s.engine_args)

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
                    else:
                        file_names = []
                        for f in self.engine.files(ts):
                            file_names.append('%s (%s)' % (f['path'], _humanizeSize(f['size'])))
                        chosen = xbmcgui.Dialog().select('TorrServer', file_names)
                        if chosen < 0:
                            return
                        sort_index = chosen

            self.file_id = sort_index
            self.engine.start(sort_index)

            self._overlay = Overlay(hash=self.engine.hash, index=self.file_id) if use_overlay else None

            if self.prebuffer():
                _log('Prebuffer success')

                playable_url = self.engine.play_url(sort_index)
                handle = int(sys.argv[1])
                list_item = xbmcgui.ListItem(path=playable_url)

                if art:
                    if callable(art):
                        art = art()
                    if isinstance(art, dict):
                        list_item.setArt(art)

                xbmcplugin.setResolvedUrl(handle, True, list_item)

                self.loop()

            if not s.save_in_database:
                _log("Remove from DB")
                self.engine.rem()

        except BaseException as e:
            _log('************************ ERROR ***********************')
            _log(e)

    def prebuffer(self):
        from .preload import PreloadDialog
        dialog = PreloadDialog(engine=self.engine, index=self.file_id)
        return dialog.run()

    def loop(self):
        _monitor = xbmc.Monitor()
        while not _monitor.abortRequested() and not self.isPlaying():
            if _monitor.waitForAbort(0.1):
                return

        _log('************************ START Playing ***********************')

        while not _monitor.abortRequested() and self.isPlaying():
            if _monitor.waitForAbort(1):
                return
            if self._overlay and self._overlay.visible:
                self._overlay.update()

        _log('************************ FINISH Playing ***********************')

    def __del__(self):
        if self._overlay:
            self._overlay.hide()

    def onPlayBackPaused(self):
        if self._overlay:
            self._overlay.show()

    def onPlayBackResumed(self):
        if self._overlay:
            self._overlay.hide()

    def onPlayBackEnded(self):
        if self._overlay:
            self._overlay.hide()

    def onPlayBackStopped(self):
        if self._overlay:
            self._overlay.hide()
