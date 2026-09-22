# coding: utf-8

from __future__ import absolute_import

import time
import sys
import xbmc, xbmcgui, xbmcaddon

from .overlay import _humanizeSize
from .player import OurDialogProgress

_addon = xbmcaddon.Addon(id='script.module.torrserver')
_locString = _addon.getLocalizedString


def format_ffprobe(data):
    if not data:
        return None
    parts = []
    fmt = data.get('format', {})
    streams = data.get('streams', [])
    video_stream = None
    audio_stream = None
    for s in streams:
        if s.get('codec_type') == 'video' and video_stream is None:
            video_stream = s
        elif s.get('codec_type') == 'audio' and audio_stream is None:
            audio_stream = s
    if video_stream:
        codec = video_stream.get('codec_name', '')
        w = video_stream.get('width', 0)
        h = video_stream.get('height', 0)
        if codec and w and h:
            parts.append('{} {}x{}'.format(codec.upper(), w, h))
        elif codec:
            parts.append(codec.upper())
    duration = fmt.get('duration', '')
    if duration:
        try:
            secs = int(float(duration))
            mins, secs = divmod(secs, 60)
            hours, mins = divmod(mins, 60)
            if hours:
                parts.append('{}:{:02d}:{:02d}'.format(hours, mins, secs))
            else:
                parts.append('{}:{:02d}'.format(mins, secs))
        except (ValueError, TypeError):
            pass
    bitrate = fmt.get('bit_rate', '')
    if bitrate:
        try:
            parts.append(_humanizeSize(int(bitrate) // 8) + '/s')
        except (ValueError, TypeError):
            pass
    if audio_stream:
        acodec = audio_stream.get('codec_name', '')
        channels = audio_stream.get('channels', 0)
        if acodec and channels:
            parts.append('{} {}ch'.format(acodec.upper(), channels))
        elif acodec:
            parts.append(acodec.upper())
    return ' | '.join(parts) if parts else None


class PreloadDialog:

    def __init__(self, engine, index=None):
        ''' index: 0-based file index '''
        self._engine = engine
        self._index = index
        self._ffprobe_data = None
        self._ffprobe_done = False

    def run(self):
        pDialog = OurDialogProgress()
        pDialog.create('TorrServer', _locString(30021))

        player = xbmc.Player()
        started_at = time.time()
        min_display = 2.0
        timeout = 0
        max_timeout = 120

        while True:
            if pDialog.iscanceled():
                pDialog.close()
                return False

            if timeout > max_timeout:
                pDialog.close()
                return False

            time.sleep(0.5)
            timeout += 0.5

            try:
                st = self._engine.stat()
            except Exception:
                continue

            if 'message' in st:
                continue

            stat_id = st.get('TorrentStatus', -1)

            if stat_id > 3:
                pDialog.close()
                return False

            if stat_id >= 2 and not self._ffprobe_done:
                self._ffprobe_done = True
                if self._index is not None:
                    try:
                        self._ffprobe_data = self._engine.ffprobe(self._index)
                    except Exception:
                        self._ffprobe_data = None

            downSpeed = st.get('DownloadSpeed', 0)
            downSpeedH = _humanizeSize(downSpeed)
            preloadedBytes = st.get('PreloadedBytes', 0)
            preloadSize = st.get('PreloadSize', 0)

            line1 = format_ffprobe(self._ffprobe_data)
            if not line1:
                line1 = _locString(30021)  # Wait for info...

            line2 = _locString(30022).format(
                st.get('ConnectedSeeders', 0),
                st.get('ActivePeers', 0),
                st.get('TotalPeers', 0))

            video_bitrate = self._get_video_bitrate()
            coeff = ''
            if downSpeed > 0 and video_bitrate > 0:
                coeff = ' [{:.2f}x]'.format((downSpeed * 8) / video_bitrate)

            line3 = u'{0}/s{1} [{2}/{3}]'.format(
                downSpeedH,
                coeff,
                _humanizeSize(preloadedBytes),
                _humanizeSize(preloadSize))

            if preloadSize > 0 and preloadedBytes > 0:
                prc = preloadedBytes * 100 / preloadSize
                if prc > 100:
                    prc = 100
                pDialog.update(int(prc), line1 + '\n' + line2, line3)

                if preloadedBytes >= preloadSize:
                    pDialog.close()
                    return True
            else:
                pDialog.update(0, line1 + '\n' + line2, line3)

            elapsed = time.time() - started_at
            if elapsed > min_display and player.isPlayingVideo():
                pDialog.close()
                return True

        return False

    def _get_video_bitrate(self):
        if not self._ffprobe_data:
            return 0
        fmt = self._ffprobe_data.get('format', {})
        bit_rate = fmt.get('bit_rate', '')
        if bit_rate:
            try:
                return int(bit_rate)
            except (ValueError, TypeError):
                pass
        streams = self._ffprobe_data.get('streams', [])
        for s in streams:
            if s.get('codec_type') == 'video':
                br = s.get('bit_rate', '')
                if br:
                    try:
                        return int(br)
                    except (ValueError, TypeError):
                        pass
        return 0
