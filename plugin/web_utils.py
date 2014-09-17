# encoding: utf-8
# web_utils.py
# Maintainer:   Brook Hong
# License:
# Copyright (c) Brook Hong.

import urllib, urllib2, json

def request(url, headers, data=None, httpErrorHandler=None, json_decode=True):
    req = urllib2.Request(url, data)
    for k in headers.keys():
        req.add_header(k, headers[k])
    try:
        response = urllib2.urlopen(req)
        jstr = response.read()
    except urllib2.HTTPError, e:
        jstr = '{"error": "%s"}' % e
        if httpErrorHandler:
            httpErrorHandler(e)
    except urllib2.URLError, e:
        jstr = '{"error": "%s"}' % e
    ret = jstr
    if json_decode:
        ret = json.loads(jstr)
    return ret
