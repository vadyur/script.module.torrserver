import threading
import xbmc, xbmcaddon
from restreamer import start_server

_addon = xbmcaddon.Addon(id='script.module.torrserver')
use_https = _addon.getSetting('use_https') == 'true'

if __name__ == '__main__':
    monitor = xbmc.Monitor()

    if use_https:
        xbmc.log('Starting TorrServer Restreamer')

        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

        xbmc.sleep(1000)

    # Wait for abort request
    while not monitor.abortRequested():
        if monitor.waitForAbort(20):
            # Abort was requested while waiting. We should exit
            if use_https and start_server.server:
                xbmc.log('Stopping TorrServer Restreamer')
                start_server.server.shutdown()
            break
