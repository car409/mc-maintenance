#!/usr/bin/env python

import usage
import sys
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler


class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        chart = usage.GenerateChart()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-length', len(chart))
        self.end_headers()
        self.wfile.write(chart)
        
        
HandlerClass = MyHandler
ServerClass  = BaseHTTPServer.HTTPServer
Protocol     = "HTTP/1.0"

if sys.argv[1:]:
    port = int(sys.argv[1])
else:
    port = 8000
server_address = ('0.0.0.0', port)

HandlerClass.protocol_version = Protocol
httpd = ServerClass(server_address, HandlerClass)

sa = httpd.socket.getsockname()
print "Serving HTTP on", sa[0], "port", sa[1], "..."
httpd.serve_forever()
