import socketserver
import requests
import http.server

PORT = 41782

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Ожидаемый путь: /https/<server>:<port>
        if self.path.startswith('/https/'):
            target = self.path[len('/https/'):]
            url = f'https://{target}'

            # Получаем заголовки клиента
            headers = {}
            if 'Range' in self.headers:
                headers['Range'] = self.headers['Range']
            if 'User-Agent' in self.headers:
                headers['User-Agent'] = self.headers['User-Agent']

            try:
                # Проксируем запрос, отключая проверку SSL
                resp = requests.get(url, stream=True, verify=False, headers=headers)
                self.send_response(resp.status_code)
                for k, v in resp.headers.items():
                    # Не отправляем Transfer-Encoding, иначе будут проблемы с body
                    if k.lower() != 'transfer-encoding':
                        self.send_header(k, v)
                self.end_headers()
                for chunk in resp.iter_content(chunk_size=8192):
                    self.wfile.write(chunk)
            except Exception as e:
                self.send_error(502, f'Bad Gateway: {url}')
        else:
            self.send_error(404, f'Not Found: {self.path}')

    def log_message(self, format, *args):
        # Отключаем логирование в консоль
        return

def start_server():
    start_server.server = None
    with socketserver.ThreadingTCPServer(('', PORT), ProxyHandler) as httpd:
        print(f"Serving at port {PORT}")
        start_server.server = httpd
        httpd.serve_forever()

if __name__ == '__main__':
    start_server()
