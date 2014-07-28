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

function! CloudBoard#UrlEncode(str, dir)
    python << EOF
import urllib
astr = vim.eval('a:str')
dir = int(vim.eval('a:dir'))
if dir:
    urlStr = urllib.quote_plus(astr)
    vim.command(('let l:urlStr="%s"') % urlStr)
else:
    urlStr = urllib.unquote_plus(astr).split('\n')
    vim.vars['cloudBoard_clip'] = urlStr
    vim.command(("let l:urlStr=g:cloudBoard_clip"))
EOF
    if type(l:urlStr) == type([])
        let l:tmp = join(l:urlStr, "\n")
        return l:tmp
    endif
    return l:urlStr
endfunction

function! CloudBoard#UrlEncodeRange(line1, line2, dir)
    let l:str = join(getline(a:line1, a:line2), "\n")
    return CloudBoard#UrlEncode(l:str, a:dir)
endfunction

function! CloudBoard#Init()
    if <SID>LoadCloudBoard() == 1
        exec 'python cloudBoard.initToken()'
    endif
endfunction

function! CloudBoard#Yank(nr, str)
    if <SID>LoadCloudBoard() == 1
        exec 'python cloudBoard.editComment('.a:nr.',"'.a:str.'")'
    endif
endfunction

function! CloudBoard#Put(nr)
    if <SID>LoadCloudBoard() == 1
        exec 'python vim.vars["cloudBoard_clip"] = cloudBoard.readComment('.a:nr.')'
        python vim.command('let @*=g:cloudBoard_clip')
        let @c = CloudBoard#UrlEncode(@*, 0)
        if @c != ""
            normal "cp
        endif
    endif
endfunction

function! s:UrlEncodeRange(line1, line2, dir)
    let @z = CloudBoard#UrlEncodeRange(a:line1, a:line2, a:dir)."\n"
    exec a:line1.','.a:line2.'d'
    normal "zP
endfunction

com! -nargs=* -range=% UrlEncode :call <SID>UrlEncodeRange(<line1>,<line2>,1)
com! -nargs=* -range=% UrlDecode :call <SID>UrlEncodeRange(<line1>,<line2>,0)

com! -nargs=0 CBInit :call CloudBoard#Init()
com! -nargs=1 -range=% CBYank :call CloudBoard#Yank(<f-args>, CloudBoard#UrlEncodeRange(<line1>, <line2>, 1))
com! -nargs=1 CBPut :call CloudBoard#Put(<f-args>)

nnoremap <space>p0 :CBPut 0<CR>
