# encoding: utf-8
# internal.py -  a very simple http server to post/get data with shelve db
#
# Maintainer:   Brook Hong
# License:
# Copyright (c) Brook Hong.  Distributed under the same terms as Vim itself.
# See :help license

#  python plugin/internal.py -p 8080 -a brookhong:123
#  curl -s -H "Authorization:Basic YnJvb2tob25nOjEyMw==" http://127.0.0.1:8080/a
#  curl -s -H "Authorization:Basic YnJvb2tob25nOjEyMw==" --data "happy birthday" http://127.0.0.1:8080/a
#  curl -s -H "Authorization:Basic YnJvb2tob25nOjEyMw==" --data "good more" http://127.0.0.1:8080/a?append=1
import os.path, sys

if sys.version_info[0] == 2:
    import BaseHTTPServer
    import urlparse
else:
    import http.server as BaseHTTPServer
    import urllib.parse as urlparse
import sys, signal
import base64
import shelve

class StoreHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    secret_key = ""
    db_file = os.getenv("HOME") + '/.cloudboard'

    def do_AUTHHEAD(self):
        print("send header")
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        if self.secret_key == "" or self.headers.getheader('Authorization') == 'Basic '+self.secret_key:
            self.send_response(200)
            self.end_headers()

            urlpath = urlparse.urlparse(self.path)
            shelve_db = shelve.open(self.db_file)
            if 'has_key' in shelve_db and shelve_db.has_key(urlpath.path) or urlpath.path in shelve_db:
                self.wfile.write(shelve_db[urlpath.path].encode())
            shelve_db.close()
        else:
            self.do_AUTHHEAD()
            self.wfile.write('no auth header received')

    def do_POST(self):
        if self.secret_key == "" or self.headers.getheader('Authorization') == 'Basic '+self.secret_key:
            length = self.headers['content-length']
            data = self.rfile.read(int(length))

            urlpath = urlparse.urlparse(self.path)
            query_components = urlparse.parse_qs(urlpath.query)
            shelve_db = shelve.open(self.db_file)
            if 'append' in query_components and query_components['append'][0] == "1":
                if 'has_key' in shelve_db and shelve_db.has_key(urlpath.path) or urlpath.path in shelve_db:
                    orig = shelve_db[urlpath.path]
                    data = orig + data
                shelve_db[urlpath.path] = data.decode()
            else:
                shelve_db[urlpath.path] = data.decode()
            shelve_db.close()
            self.send_response(200)
            self.end_headers()
        else:
            self.do_AUTHHEAD()
            self.wfile.write('no auth header received')

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-p", "--port", dest="port",
            help="listen on PORT, default as 8080", metavar="PORT")
    parser.add_option("-a", "--auth", dest="auth",
            help="use AUTH as basic authentication, like 'brookhong:123'", metavar="AUTH")
    parser.add_option("-f", "--file", dest="db_file",
            help="use FILE as a db file to store data, default as ~/.cloudboard", metavar="FILE")

    (options, args) = parser.parse_args()
    port = 8080
    if options.port:
        port = int(options.port)

    if options.auth:
        StoreHandler.secret_key = base64.b64encode(options.auth)
        print("auth_code: " + StoreHandler.secret_key)

    if options.db_file:
        StoreHandler.db_file = options.db_file

    signal.signal(signal.SIGINT, signal_handler)

    httpd = BaseHTTPServer.HTTPServer(('', port), StoreHandler)
    sa = httpd.socket.getsockname()
    print("Serving HTTP on", sa[0], "port", sa[1], "...")
    httpd.serve_forever()
