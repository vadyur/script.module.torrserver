# coding: utf-8

from __future__ import absolute_import

import os
import sys
from typing import Dict, List, Optional, Tuple
import xbmc, xbmcgui, xbmcaddon

from .engine import Engine
from .settings import Settings

_addon = xbmcaddon.Addon(id='script.module.torrserver')
_locString = _addon.getLocalizedString


if sys.version_info >= (3, 0):
    def _fs_dec(path):
        return path
else:
    def _fs_dec(path):
        sys_enc = sys.getfilesystemencoding() if sys.getfilesystemencoding() else 'utf-8'
        return path.decode(sys_enc).encode('utf-8')


def _get_language() -> str:
    try:
        lang = xbmc.getLanguage(xbmc.ISO_639_1, True)
        if not lang:
            lang = "en"
        return lang
    except Exception:
        return "en"


_UNITS: Dict[str, List[str]] = {
    "en": ["B", "KB", "MB", "GB", "TB"],
    "ru": ["Б", "Кб", "Мб", "Гб", "Тб"],
}


def _humanizeSize(size):
    UNITS = _UNITS.get(_get_language())
    if UNITS is None:
        UNITS = _UNITS['en']

    HUMANFMT = "%.2f %s"
    HUMANRADIX = 1024.

    for u in UNITS[:-1]:
        if size < HUMANRADIX:
            return HUMANFMT % (size, u)
        size /= HUMANRADIX

    return HUMANFMT % (size, UNITS[-1])


class Overlay:

    def __init__(self, hash: str, index: Optional[int] = None):
        ''' index: 0-based file index, None - whole torrent '''
        self._hash = hash
        self._index = index

        s = Settings()
        self._engine = Engine(**s.engine_args)
        self._engine.hash = hash

        width, height = self._get_skin_resolution()
        w = width
        h = int(0.14 * height)
        x = 0
        y = int((height - h) / 2)
        self._window = xbmcgui.Window(12005)
        self._label = xbmcgui.ControlLabel(x, y, w, h, '', alignment=6)
        self._background = xbmcgui.ControlImage(x, y, w, h, _fs_dec(self._get_ov_image()))
        self._background.setColorDiffuse('0xD0000000')
        self.visible = False

    def show(self):
        if not self.visible:
            self._window.addControls([self._background, self._label])
            self._window.setProperty('torrserve_overlay_active', '1')
            self.visible = True

    def hide(self):
        if self.visible:
            self._window.removeControls([self._background, self._label])
            self._window.clearProperty('torrserve_overlay_active')
            self.visible = False

    def update(self):
        if not self.visible:
            return

        try:
            info = self._engine.stat()

            downloaded = int(info.get('LoadedSize', 0))
            dl_speed = int(info.get('DownloadSpeed', 0))
            if self._index is not None:
                try:
                    size = int(info.get('FileStats', [])[self._index].get('Length', 0))
                except (IndexError, AttributeError):
                    size = 0
            else:
                size = int(info.get('TorrentSize', 0))
            if size <= 0:
                return

            percent = float(downloaded) * 100 / size
            player = xbmc.Player()
            percendSpeed = dl_speed * player.getTotalTime() / size

            heading = "{}: {} {} {} - {}% ({})".format(
                _locString(30010),  # Downloaded
                _humanizeSize(downloaded),
                _locString(30011),  # from
                _humanizeSize(size),
                int(percent),
                _humanizeSize(size)) + '\n'
            if percent:
                heading += "{}: {}/{} [{:.2f}x]\n".format(
                    _locString(30012),  # Speed
                    _humanizeSize(dl_speed),
                    "sec",
                    percendSpeed)
                heading += "{}: {} | {}: {} | {}: {}".format(
                    _locString(30013),  # Seeders
                    info.get('ConnectedSeeders', 0),
                    _locString(30014),  # Active
                    info.get('ActivePeers', 0),
                    _locString(30015),  # Total
                    info.get('TotalPeers', 0))

            self._label.setLabel(heading)
        except Exception as e:
            xbmc.log('Overlay.update error: {}'.format(str(e)), xbmc.LOGDEBUG)

    @staticmethod
    def _get_ov_image():
        ov_image = _fs_dec(os.path.join(_addon.getAddonInfo('path'), 'bg.png'))
        if not os.path.isfile(ov_image):
            import base64
            with open(ov_image, 'wb') as fl:
                fl.write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='))
        return ov_image

    @staticmethod
    def _get_skin_resolution() -> Tuple[int, int]:
        ''' Координатная сетка скина. Kodi берёт из <res> скина разрешение с соотношением сторон,
            ближайшим к экрану; первый <res> часто 4:3 (1920x1440), из-за чего полоса уезжала вниз.
        '''
        import xml.etree.ElementTree as Et
        from xbmcvfs import translatePath
        skin_path = translatePath('special://skin/')
        tree = Et.parse(os.path.join(skin_path, 'addon.xml'))
        resolutions = [(int(r.attrib['width']), int(r.attrib['height']), r.attrib.get('default') == 'true')
                       for r in tree.findall('./extension/res')]

        try:
            screen_w = int(xbmc.getInfoLabel('System.ScreenWidth'))
            screen_h = int(xbmc.getInfoLabel('System.ScreenHeight'))
        except ValueError:
            screen_w = screen_h = 0

        if screen_w and screen_h:
            aspect = float(screen_w) / screen_h
            w, h, _ = min(resolutions, key=lambda r: abs(float(r[0]) / r[1] - aspect))
            return w, h

        for w, h, default in resolutions:
            if default:
                return w, h
        return resolutions[0][0], resolutions[0][1]
