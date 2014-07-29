# encoding: utf-8
# cloudboard.vim -  a cloud-based clipboard, yank text into a numbered cloud register on a machine,
#                   put the text from the cloud register on another machine.
# Maintainer:   Brook Hong
# License:
# Copyright (c) Brook Hong.  Distributed under the same terms as Vim itself.
# See :help license

import urllib, urllib2, base64
import json,os

def request(url, headers, data=None, httpErrorHandler=None):
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
    return json.loads(jstr)

def initToken(username, password):
    basicAuth = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    tokens = request('https://api.github.com/authorizations', {"Authorization": "Basic %s" % basicAuth})
    token = ""
    if "error" not in tokens:
        for t in tokens:
            if t['note'] == "cloudboard" and 'gist' in t['scopes']:
                token = str(t['token'])
                break
        if token == "":
            t = request('https://api.github.com/authorizations', {'Authorization': "Basic %s" % basicAuth}, '{ "scopes": [ "gist" ], "note": "cloudboard" }')
            token = str(t['token'])
    return token

def initGist(token, name):
    gists = request('https://api.github.com/gists', {'Authorization': 'token %s' % token})
    gist = ""
    for g in gists:
        if g['description'] == name and name in g['files']:
            gist = str(g['id'])
            break
    if gist == "":
        g = request('https://api.github.com/gists', {'Authorization': 'token %s' % token}, '{ "description": "%s", "public": false, "files": { "%s": { "content": "%s" } } }' % (name, name, name))
        gist = str(g['id'])
    return gist

def module_exists(module_name):
    try:
        __import__(module_name)
    except ImportError:
        return False
    else:
        return True

class CloudBoard:
    def __init__(self):
        self.configFN = os.getenv("HOME").replace("\\","/")+"/.cloudboard.json"
        if os.path.isfile(self.configFN):
            configFile = open(self.configFN, 'r')
            jstr = configFile.read()
            configFile.close()
            try:
                self.config = json.loads(jstr)
            except ValueError:
                self.config = {}
        else:
            self.config = {}

    def saveConfig(self):
        configFile = open(self.configFN, 'w')
        configFile.write(json.dumps(self.config))
        configFile.close()

    def initToken(self):
        ret = False
        if module_exists("vim"):
            vim.command("let g:cloudBoardOwn=input('To use CloudBoard, you need set up your exclusive one.\nUse your own GITHUB account(Y/N)?', 'Y')")
            if vim.eval('g:cloudBoardOwn') == 'Y':
                vim.command("let g:cloudBoardUser=input('GITHUB username:')")
                vim.command("let g:cloudBoardPass=input('GITHUB password:')")
                self.config['token'] = initToken(vim.eval( 'g:cloudBoardUser' ), vim.eval( 'g:cloudBoardPass' ))
                if self.config['token'] == "":
                    vim.command('echo "\nInvalid GITHUB account!"')
                else:
                    self.config['gist'] = initGist(self.config['token'], "cloudboard.%s" % (vim.eval( 'g:cloudBoardUser' )))
                    ret = True
                vim.command("unlet g:cloudBoardUser")
                vim.command("unlet g:cloudBoardPass")
            else:
                self.config['token'] = '1012d87ff4b053d01ce2f90bd266f2a047567bd3';
                vim.command("let g:cloudBoardEmail=input('An unique name for your CloudBoard(Your Email Address preferred):')")
                if vim.eval( 'g:cloudBoardEmail' ) != "":
                    self.config['gist'] = initGist(self.config['token'], "cloudboard.%s" % (vim.eval( 'g:cloudBoardEmail' )))
                    ret = True
                else:
                    vim.command('echo "\nCloudBoard name is better to be unique!"')
                vim.command("unlet g:cloudBoardEmail")
            vim.command("unlet g:cloudBoardOwn")

        if ret:
            self.config['comments'] = []
            self.saveConfig()
        return ret

    def commentsErrorHandler(self, e):
        if e.code == 404:
            self.listComments(['id'])
            print "Fixed CloudBoard ID error, please try again."
        elif e.code == 401:
            self.initToken()
        else:
            print e

    def listComments(self, fields):
        if 'token' not in self.config or 'gist' not in self.config:
            self.initToken()
        comments = []
        if 'gist' in self.config:
            comments = request('https://api.github.com/gists/%s/comments' % self.config['gist'], {'Authorization': 'token %s' % self.config['token']})
            self.config['comments'] = map(lambda c: [c['id']], comments)
            self.saveConfig()
            comments = map(lambda c: [c[k] for k in fields], comments)
        return comments

    def newComment(self, clip):
        return request('https://api.github.com/gists/%s/comments' % self.config['gist'], {'Authorization': 'token %s' % self.config['token']}, '{ "body": "%s" }' % clip)

    def readComment(self, nr):
        if 'comments' not in self.config:
            self.listComments(['id'])
        comment = ""
        if 'comments' in self.config:
            if nr >= len(self.config['comments']):
                self.listComments(['id'])
            if nr < len(self.config['comments']):
                cid = self.config['comments'][nr][0]
                cmt = request('https://api.github.com/gists/%s/comments/%s' % (self.config['gist'], cid), {'Authorization': 'token %s' % self.config['token']}, httpErrorHandler=self.commentsErrorHandler)
                if "error" not in cmt:
                    comment = cmt['body'].encode('utf8')
        return comment

    def editComment(self, nr, clip):
        if 'comments' not in self.config:
            self.listComments(['id'])
        if 'comments' in self.config:
            if nr >= len(self.config['comments']):
                self.listComments(['id'])
            if nr >= len(self.config['comments']):
                i = 0
                j = nr-len(self.config['comments'])+1
                while i<j:
                    self.newComment(".")
                    i = i+1
                self.listComments(['id'])
            cid = self.config['comments'][nr][0]
            return request('https://api.github.com/gists/%s/comments/%s' % (str(self.config['gist']), cid),
                    {'Authorization': 'token %s' % str(self.config['token'])}, '{ "body": "%s" }' % clip,
                    httpErrorHandler=self.commentsErrorHandler)
        return {"error": "not ready"}

    def clearComments(self):
        self.listComments(['id'])
        for c in self.config['comments']:
            cid = c[0]
            request('https://api.github.com/gists/%s/comments/%s' % (str(self.config['gist']), cid), {'Authorization': 'token %s' % str(self.config['token'])}, '{"body": "."}')
        self.saveConfig()

cloudBoard = CloudBoard()
