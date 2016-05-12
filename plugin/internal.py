# encoding: utf-8
# internal.py -  a very simple http server to post/get data with shelve db
#
# Maintainer:   Brook Hong
# License:
# Copyright (c) Brook Hong.  Distributed under the same terms as Vim itself.
# See :help license

#  python plugin/internal.py 8080 brookhong:123
#  curl -s -H "Authorization:Basic YnJvb2tob25nOjEyMw==" http://127.0.0.1:8080/a
#  curl -s -H "Authorization:Basic YnJvb2tob25nOjEyMw==" --data "happy birthday" http://127.0.0.1:8080/a
#  curl -s -H "Authorization:Basic YnJvb2tob25nOjEyMw==" --data "good more" http://127.0.0.1:8080/a?append=1
import os.path;

import BaseHTTPServer
import sys, signal
import base64
import shelve
from urlparse import urlparse, parse_qs

class StoreHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    shelve_db = shelve.open("./internal_board")
    secret_key = ""

    def do_AUTHHEAD(self):
        print "send header"
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        if self.secret_key != "" and self.headers.getheader('Authorization') == 'Basic '+self.secret_key:
            self.send_response(200)
            self.end_headers()

            urlpath = urlparse(self.path)
            if self.shelve_db.has_key(urlpath.path):
                self.wfile.write(self.shelve_db[urlpath.path].encode())
        else:
            self.do_AUTHHEAD()
            self.wfile.write('no auth header received')

    def do_POST(self):
        if self.secret_key != "" and self.headers.getheader('Authorization') == 'Basic '+self.secret_key:
            length = self.headers['content-length']
            data = self.rfile.read(int(length))

            urlpath = urlparse(self.path)
            query_components = parse_qs(urlpath.query)
            if 'append' in query_components and query_components['append'][0] == "1":
                orig = self.shelve_db[urlpath.path]
                data = orig + data
                self.shelve_db[urlpath.path] = data.decode()
            else:
                self.shelve_db[urlpath.path] = data.decode()
            self.send_response(200)
        else:
            self.do_AUTHHEAD()
            self.wfile.write('no auth header received')

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)

if __name__ == '__main__':
    if len(sys.argv)<2:
        print "usage internal.py [port] [username:password]"
        sys.exit()
    if len(sys.argv) == 3:
        StoreHandler.secret_key = base64.b64encode(sys.argv[2])
        print "auth_code: " + StoreHandler.secret_key

    signal.signal(signal.SIGINT, signal_handler)
    BaseHTTPServer.test(StoreHandler, BaseHTTPServer.HTTPServer)
