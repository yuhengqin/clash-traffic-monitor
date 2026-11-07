import unittest
import http.server
import threading
import urllib.error
import urllib.request
from gateway import classify_request, request_origin_allowed, Handler, TARGETS

class GatewayPolicyTest(unittest.TestCase):
    def test_unreachable_remote_produces_gateway_error(self):
        previous = TARGETS['lenovo']
        TARGETS['lenovo'] = 'http://127.0.0.1:1'
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            url = 'http://127.0.0.1:%s/api/traffic/aggregate' % server.server_port
            req = urllib.request.Request(url, headers={'Host':'127.0.0.1:18081', 'X-Traffic-Source':'lenovo'})
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=3)
            self.assertEqual(error.exception.code, 502)
        finally:
            server.shutdown(); server.server_close(); worker.join(); TARGETS['lenovo'] = previous
    def test_cross_site_navigation_only_for_top_level_dashboard(self):
        self.assertTrue(request_origin_allowed('', '127.0.0.1:18081', 'cross-site', 'navigate', 'document', '/'))
        self.assertFalse(request_origin_allowed('', '127.0.0.1:18081', 'cross-site', 'cors', 'empty', '/api/traffic/aggregate'))
        self.assertFalse(request_origin_allowed('', '127.0.0.1:18081', 'cross-site', 'navigate', 'iframe', '/'))
    def test_routes(self):
        self.assertEqual(classify_request('GET', '/api/traffic/aggregate', 'local'), 'local')
        self.assertEqual(classify_request('PUT', '/api/settings/mihomo', 'local'), 'local')
        self.assertEqual(classify_request('GET', '/api/traffic/aggregate', 'lenovo'), 'lenovo')
        self.assertIsNone(classify_request('GET', '/api/settings/mihomo', 'lenovo'))
        self.assertIsNone(classify_request('DELETE', '/api/traffic/logs', 'lenovo'))
        self.assertIsNone(classify_request('GET', '/api/traffic/../settings/mihomo', 'lenovo'))
        self.assertIsNone(classify_request('GET', '/api/traffic/aggregate', 'unknown'))

if __name__ == '__main__': unittest.main()
