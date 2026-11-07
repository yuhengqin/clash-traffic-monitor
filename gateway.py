"""Local, read-only source switcher; existing collectors remain independent."""
import http.server
import pathlib
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent / 'web'
TRAFFIC_PATHS = frozenset('/api/traffic/' + s for s in (
    'aggregate', 'substats', 'proxy-stats', 'devices-by-host',
    'devices-by-proxy-host', 'details', 'trend', 'logs'))
TARGETS = {'local': 'http://127.0.0.1:18080', 'lenovo': 'http://192.168.0.105:18080'}
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def classify_request(method, path, source):
    if source == 'local' and path.startswith('/api/') and '..' not in path:
        return 'local'
    if source == 'lenovo' and method == 'GET' and path in TRAFFIC_PATHS:
        return 'lenovo'
    return None

def request_origin_allowed(origin, host, site, mode, dest, path):
    if origin and origin != 'http://' + host: return False
    if site == 'cross-site':
        return mode == 'navigate' and dest == 'document' and path in ('/', '/index.html')
    return True

class Handler(http.server.BaseHTTPRequestHandler):
    def handle_request(self):
        host = self.headers.get('Host', '')
        origin = self.headers.get('Origin', '')
        path = urllib.parse.urlsplit(self.path).path
        if host not in ('127.0.0.1:18081', 'localhost:18081') or not request_origin_allowed(origin, host, self.headers.get('Sec-Fetch-Site'), self.headers.get('Sec-Fetch-Mode'), self.headers.get('Sec-Fetch-Dest'), path):
            self.send_error(403); return
        url = urllib.parse.urlsplit(self.path)
        if url.path.startswith('/api/'):
            source = self.headers.get('X-Traffic-Source', 'local')
            if not classify_request(self.command, url.path, source):
                self.send_error(403); return
            request_body = None
            if self.command not in ('GET', 'HEAD'):
                try: length = int(self.headers.get('Content-Length', '0'))
                except ValueError: self.send_error(400); return
                if length < 0 or length > 1048576: self.send_error(413); return
                request_body = self.rfile.read(length)
            req = urllib.request.Request(TARGETS[source] + url.path + (('?' + url.query) if url.query else ''), data=request_body, method=self.command, headers={'Content-Type': self.headers.get('Content-Type', 'application/json')})
            try: response = OPENER.open(req, timeout=5)
            except urllib.error.HTTPError as e: response = e
            except (OSError, urllib.error.URLError): self.send_error(502, 'Data source unavailable'); return
            with response:
                body = response.read()
                self.send_response(response.status)
                self.send_header('Content-Type', response.headers.get('Content-Type', 'application/json'))
                self.send_header('Content-Length', str(len(body)))
                self.end_headers(); self.wfile.write(body)
            return
        if self.command != 'GET' or url.path not in ('/', '/index.html', '/app.js', '/styles.css', '/favicon.svg'):
            self.send_error(404); return
        name = 'index.html' if url.path == '/' else url.path.lstrip('/')
        body = (ROOT / name).read_bytes()
        kind = {'html':'text/html; charset=utf-8', 'js':'text/javascript; charset=utf-8', 'css':'text/css; charset=utf-8', 'svg':'image/svg+xml'}[name.rsplit('.', 1)[-1]]
        self.send_response(200); self.send_header('Content-Security-Policy', "frame-ancestors 'none'"); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    do_GET = handle_request
    do_PUT = handle_request
    do_DELETE = handle_request
    def log_message(self, *args): pass

if __name__ == '__main__':
    http.server.ThreadingHTTPServer(('127.0.0.1', 18081), Handler).serve_forever()
