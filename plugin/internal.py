from os import curdir
import os.path;

import BaseHTTPServer
import sys
import base64


class StoreHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    secret_key = ""

    def do_AUTHHEAD(self):
        print "send header"
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        if self.secret_key != "" and self.headers.getheader('Authorization') == 'Basic '+self.secret_key:
            fn = "./" + self.path
            if os.path.isfile(fn):
                with open(fn) as fh:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/json')
                    self.end_headers()
                    self.wfile.write(fh.read().encode())
            self.send_response(200)
        else:
            self.do_AUTHHEAD()
            self.wfile.write('no auth header received')

    def do_POST(self):
        if self.secret_key != "" and self.headers.getheader('Authorization') == 'Basic '+self.secret_key:
            length = self.headers['content-length']
            data = self.rfile.read(int(length))

            with open("./" + self.path, 'w+') as fh:
                fh.write(data.decode())

            self.send_response(200)
        else:
            self.do_AUTHHEAD()
            self.wfile.write('no auth header received')


if __name__ == '__main__':
    if len(sys.argv)<2:
        print "usage internal.py [port] [username:password]"
        sys.exit()
    if len(sys.argv) == 3:
        StoreHandler.secret_key = base64.b64encode(sys.argv[2])
        print "auth_code: " + StoreHandler.secret_key
    BaseHTTPServer.test(StoreHandler, BaseHTTPServer.HTTPServer)
