" cloudboard.vim -  a cloud-based clipboard, yank text into a numbered cloud register on a machine,
"                   put the text from the cloud register on another machine.
" Maintainer:   Brook Hong
" License:
" Copyright (c) Brook Hong.  Distributed under the same terms as Vim itself.
" See :help license

if !has("python")
    finish
endif

let s:cloudboard_py = expand("<sfile>:p:h")."/cloudboard.py"

exec 'pyfile '.expand("<sfile>:p:h")."/web_utils.py"

let s:cloudboard_py_loaded = 0
function! s:LoadCloudBoard()
    if s:cloudboard_py_loaded == 0
        if filereadable(s:cloudboard_py)
            exec 'pyfile '.s:cloudboard_py
            let s:cloudboard_py_loaded = 1
        else
            call confirm('cloudboard.vim: Unable to find '.s:cloudboard_py.'. Place it in either your home vim directory or in the Vim runtime directory.', 'OK')
        endif
    endif
    return s:cloudboard_py_loaded
endfunction

function! cloudboard#UrlEncode(str, dir)
    python << EOF
import urllib
astr = vim.eval('a:str')
dir = int(vim.eval('a:dir'))
if dir:
    urlStr = urllib.quote_plus(astr)
    vim.command(('let l:urlStr="%s"') % urlStr)
else:
    urlStr = urllib.unquote_plus(astr)
    urlStr = urlStr.replace("'", "''")
    vim.command("let l:urlStr='%s'" % urlStr)
EOF
    if type(l:urlStr) == type([])
        let l:tmp = join(l:urlStr, "\n")
        return l:tmp
    endif
    return l:urlStr
endfunction

function! cloudboard#UrlEncodeRange(line1, line2, dir)
    let l:str = join(getline(a:line1, a:line2), "\n")
    return cloudboard#UrlEncode(l:str, a:dir)
endfunction

function! cloudboard#Init()
    if <SID>LoadCloudBoard() == 1
        exec 'python cloudBoard.initToken()'
    endif
endfunction

function! cloudboard#AutoClear(nr)
    if <SID>LoadCloudBoard() == 1
        exec 'python cloudBoard.setAutoClear('.a:nr.')'
    endif
endfunction

function! cloudboard#Yank(nr, str)
    if <SID>LoadCloudBoard() == 1
        exec 'python cloudBoard.editComment('.a:nr.',"'.a:str.'")'
    endif
endfunction

function! cloudboard#Put(nr)
    if <SID>LoadCloudBoard() == 1
        exec 'python cloudBoard.readComment('.a:nr.')'
    endif
endfunction

function! cloudboard#List()
    if <SID>LoadCloudBoard() == 1
        python cloudBoard.readComments()
    endif
endfunction

function! cloudboard#Save(name, str)
    if <SID>LoadCloudBoard() == 1
        exec 'python cloudBoard.newFile("'.a:name.'","'.a:str.'")'
    endif
endfunction

function! cloudboard#Load(name)
    if <SID>LoadCloudBoard() == 1
        exec 'python cloudBoard.readFile("'.a:name.'")'
    endif
endfunction

function! cloudboard#Delete(name)
    if <SID>LoadCloudBoard() == 1
        exec 'python cloudBoard.deleteFile("'.a:name.'")'
    endif
endfunction

function! cloudboard#ListFiles()
    if <SID>LoadCloudBoard() == 1
        python cloudBoard.readFiles()
    endif
endfunction

function! s:UrlEncodeRange(line1, line2, dir)
    let @z = cloudboard#UrlEncodeRange(a:line1, a:line2, a:dir)."\n"
    exec a:line1.','.a:line2.'d'
    normal "zP
endfunction

function! cloudboard#BufffersList(A,L,P)
    let all = range(0, bufnr('$'))
    let res = []
    for b in all
        if buflisted(b)
            let a = substitute(bufname(b),"\\","\/","g")
            let a = substitute(a,".*/","","g")
            if a != ''  && count(res, a) == 0 && a =~ a:A.'.*'
                call add(res, a)
            endif
        endif
    endfor
    return res
endfunction

com! -nargs=* -range=% UrlEncode :call <SID>UrlEncodeRange(<line1>,<line2>,1)
com! -nargs=* -range=% UrlDecode :call <SID>UrlEncodeRange(<line1>,<line2>,0)

com! -nargs=0 CBInit :call cloudboard#Init()
com! -nargs=1 CBAutoClear :call cloudboard#AutoClear(<f-args>)
com! -nargs=1 -range=% CBYank :call cloudboard#Yank(<f-args>, cloudboard#UrlEncodeRange(<line1>, <line2>, 1))
com! -nargs=1 CBPut :call cloudboard#Put(<f-args>)
com! -nargs=0 CBList :call cloudboard#List()
com! -nargs=1 -complete=customlist,cloudboard#BufffersList -range=% CBSave :call cloudboard#Save(<f-args>, cloudboard#UrlEncodeRange(<line1>, <line2>, 1))
com! -nargs=1 -complete=customlist,cloudboard#BufffersList CBLoad :call cloudboard#Load(<f-args>)
com! -nargs=1 -complete=customlist,cloudboard#BufffersList CBRm :call cloudboard#Delete(<f-args>)
com! -nargs=0 CBListFiles :call cloudboard#ListFiles()
