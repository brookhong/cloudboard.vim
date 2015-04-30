# encoding: utf-8
# cloudboard.vim -  a cloud-based clipboard, yank text into a numbered cloud register on a machine,
#                   put the text from the cloud register on another machine.
# Maintainer:   Brook Hong
# License:
# Copyright (c) Brook Hong.  Distributed under the same terms as Vim itself.
# See :help license

import base64, os, sys
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

reload(sys)
sys.setdefaultencoding('utf8')

def initGist(token, name):
    gists = request('https://api.github.com/gists', {'Authorization': 'token %s' % token})
    gist = ""
    ln = len(name)
    for g in gists:
        if g['description'][:ln] == name and g['description'] in g['files']:
            gist = str(g['id'])
            break
    if gist == "":
        g = request('https://api.github.com/gists', {'Authorization': 'token %s' % token}, '{ "description": "%s", "public": false, "files": { "%s": { "content": "%s" } } }' % (name, name, token))
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
            vim.command("let g:gistToken=input('To use CloudBoard, you must generate your personal access token(https://github.com/settings/tokens), then input it here:')")
            if vim.eval('g:gistToken') != '':
                self.config['token'] = vim.eval('g:gistToken')
                self.config['gist'] = initGist(self.config['token'], "cloudboard")
                ret = True
            vim.command("unlet g:gistToken")
        return ret

    def newFile(self, name, content):
        cf = request('https://api.github.com/gists/%s' % self.config['gist'], {'Authorization': 'token %s' % self.config['token']}, '{ "files": { "%s": { "content": "%s" } } }' % (name, content))
        if "error" in cf:
            vim.command("echohl WarningMsg | echo '%s'| echohl None" % cf['error'])
        else:
            vim.command("echo 'Saved into cloud file %s.'" % name)

    def deleteFile(self, name):
        cf = request('https://api.github.com/gists/%s' % self.config['gist'], {'Authorization': 'token %s' % self.config['token']}, '{ "files": { "%s": { "content": null } } }' % name)
        if "error" in cf:
            vim.command("echohl WarningMsg | echo '%s'| echohl None" % cf['error'])
        else:
            vim.command("echo 'Deleted cloud file %s.'" % name)

    def readFile(self, name):
        content = ""
        gist = request('https://api.github.com/gists/%s' % self.config['gist'], {'Authorization': 'token %s' % self.config['token']})
        if "error" in gist:
            vim.command("echohl WarningMsg | echo '%s'| echohl None" % gist['error'])
        else:
            if "files" in gist and name in gist['files']:
                furl = gist['files'][name]['raw_url']
                content = request(furl, {'Authorization': 'token %s' % self.config['token']}, json_decode=False)
                content = urllib.unquote_plus(content).replace("'", "''")
                vim.command("let @c='%s'" % content)
                vim.command('normal "cp')
            else:
                vim.command("echo 'No such file named %s.'" % name)

    def readFiles(self):
        content = ""
        gist = request('https://api.github.com/gists/%s' % self.config['gist'], {'Authorization': 'token %s' % self.config['token']})
        if "error" in gist:
            vim.command("echohl WarningMsg | echo '%s'| echohl None" % gist['error'])
        else:
            if "files" in gist:
                for name in gist['files']:
                    furl = gist['files'][name]['raw_url']
                    cmt = request(furl, {'Authorization': 'token %s' % self.config['token']}, json_decode=False)
                    cmt = '%s %s %s\n%s\n' % ('>'*16, name, '<'*16, urllib.unquote_plus(cmt).replace("'", "''"))
                    content = content + cmt
                vim.command("let @c='%s'" % content)
                vim.command('normal "cp')

    def commentsErrorHandler(self, e):
        if e.code == 404:
            self.listComments(['id'])
            vim.command("echo 'Fixed CloudBoard ID error, please try again.'")
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
            if 'error' in comments:
                self.initToken()
            else:
                self.config['comments'] = map(lambda c: [c['id']], comments)
                self.saveConfig()
                comments = map(lambda c: [c[k] for k in fields], comments)
        return comments

    def newComment(self, clip):
        return request('https://api.github.com/gists/%s/comments' % self.config['gist'], {'Authorization': 'token %s' % self.config['token']}, '{ "body": "%s" }' % clip)

    def readComments(self):
        comments = self.listComments(['body'])
        allcomts = ""
        hid = 0
        for c in comments:
            cmt = '%s %d %s\n%s\n' % ('>'*16, hid, '<'*16, urllib.unquote_plus(c[0]).replace("'", "''"))
            allcomts = allcomts + cmt
            hid = hid + 1
        vim.command("let @c='%s'" % allcomts)
        vim.command('normal "cp')

    def setAutoClear(self, nr):
        if 'autoclear' not in self.config:
            self.config['autoclear'] = []
        if nr in self.config['autoclear']:
            self.config['autoclear'].remove(nr)
            vim.command("echo 'AutoClear has been disabled for cloud register %s.'" % nr)
        else:
            self.config['autoclear'].append(nr)
            vim.command("echo 'AutoClear has been enabled for cloud register %s.'" % nr)
        self.saveConfig()

    def readComment(self, nr):
        if 'comments' not in self.config:
            self.listComments(['id'])
        if 'comments' in self.config:
            if nr >= len(self.config['comments']):
                self.listComments(['id'])
            if nr < len(self.config['comments']):
                cid = self.config['comments'][nr][0]
                cmt = request('https://api.github.com/gists/%s/comments/%s' % (self.config['gist'], cid), {'Authorization': 'token %s' % self.config['token']}, httpErrorHandler=self.commentsErrorHandler)
                if "error" in cmt:
                    vim.command("echohl WarningMsg | echo '%s'| echohl None" % cmt['error'])
                else:
                    comment = cmt['body'].encode('utf8')
                    if len(comment) > 1:
                        comment = urllib.unquote_plus(comment).replace("'", "''")
                        vim.command("let @c='%s'" % comment)
                        vim.command('normal "cp')
                        if 'autoclear' in self.config and nr in self.config['autoclear']:
                            request('https://api.github.com/gists/%s/comments/%s' % (self.config['gist'], cid), {'Authorization': 'token %s' % self.config['token']}, '{ "body": "." }', httpErrorHandler=self.commentsErrorHandler)
                    else:
                        vim.command("echo 'No data in the cloud register.'")

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
            cmt = request('https://api.github.com/gists/%s/comments/%s' % (self.config['gist'], cid),
                    {'Authorization': 'token %s' % self.config['token']}, '{ "body": "%s" }' % clip,
                    httpErrorHandler=self.commentsErrorHandler)
            if "error" in cmt:
                vim.command("echohl WarningMsg | echo '%s'| echohl None" % cmt['error'])
            else:
                vim.command("echo 'Copied into cloud register %s.'" % nr)

    def clearComments(self):
        self.listComments(['id'])
        for c in self.config['comments']:
            cid = c[0]
            request('https://api.github.com/gists/%s/comments/%s' % (self.config['gist'], cid), {'Authorization': 'token %s' % self.config['token']}, '{"body": "."}')
        self.saveConfig()

cloudBoard = CloudBoard()
