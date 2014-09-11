# cloudboard.vim

A cloud-based clipboard, yank(copy) text into a numbered cloud register on a machine, put(paste) the text from the cloud register on another machine.

It uses GITHUB's gist as the cloud service.

# Usage

1. run command `:CBInit` to set up your own cloudboard.
2. visual select the text that you want to copy (otherwise all the current buffer), use command `:CBYank 0` to copy it into cloud register 0.
![CBYank](https://raw.githubusercontent.com/brookhong/brookhong.github.io/master/assets/images/cbyank.gif)
3. open vim on another machine, use command `:CBPut 0` to paste the text from cloud register 0.
![CBPut](https://raw.githubusercontent.com/brookhong/brookhong.github.io/master/assets/images/cbput.gif)


### Cloud Register

The number starts from 0, you can use anyone you'd like, for example:

    :CBYank 5
    :CBPut 5


`:CBList` to put the contents from all cloud registers into current buffer.

### Cloud Files

Cloud files are named files stored in a GITHUB gist.

    :CBSave test.c      to save selected range into a cloud file named test.c.
    :CBLoad test.c      to load a cloud file test.c into current buffer.
    :CBRm test.c        to delete a cloud file test.c.
    :CBListFiles        to list all cloud files in the cloudboard gist.

Loading cloud files requires two requests to GITHUB, thus cloud register is faster to be used as a clipboard across machines.
Cloud files is better when the text is huge, especial in case of that you prefer to save them for long period.

### Recommended Mappings

    nnoremap <space>p :CBPut 
    vnoremap <space>y :CBYank 

# Installation

Your VIM must have python support, check it with `:python print 'hello'`.

`Bundle 'brookhong/cloudboard.vim'`
