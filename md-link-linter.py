#!/usr/bin/env python3
from subprocess import run, PIPE
from os import chdir, walk
from tempfile import TemporaryDirectory
from shutil import rmtree
from argparse import ArgumentParser
parser = ArgumentParser('md-link-linter')
parser.add_argument('-g', '--git', action='store_true', help="lint a git repository instead of a directory")
parser.add_argument('location', nargs='+', help="the directories (or repository urls if --git) to lint")
args = parser.parse_args()
links = []
def read_until(fd, start, stop):
    fd.seek(start)
    text = ''
    char = fd.read(1)
    while char != '':
        text += char
        if char == stop:
            break
        char = fd.read(1)
    return text
def find_links(fd):
    import re
    text = ''
    line_positions = [0]
    new = read_until(fd, 0, '\n')
    while new != '':
        text += new
        line_positions.append(fd.tell())
        new = read_until(fd, fd.tell(), '\n')
    for match in re.finditer(r'!?\[([^\[\]]+)\]\((https?:\/\/[^\)]+)\)', text):
        for position in reversed(line_positions):
            if position < match.start():
                break
        context = read_until(fd, position, '\n')
        yield match.group(1), match.group(2), context
    # returns a list of matches. each match is a tuple of the form: (context, linktext, linkurl)
def check_link(link):
    return eval(run(['curl', '-s', '-o /dev/null', '-I', '-w "%{http_code}"', link], stdout=PIPE).stdout)
def find_md_files(directory):
    for dirname, dirs, files in walk(directory): # explores the directory tree
        for entry in files:
            if entry.endswith('.md'):
                yield dirname+'/'+entry
if args.git:
    for repo in args.location:
        with TemporaryDirectory() as clonedir: # create a temporary directory to clone the git repo into
            chdir(clonedir)
            run(['git','clone','-q',repo,'.'],check=True) # clone the repo into the current directory
            rmtree('.git') # remove the .git folder so that we don't have to look for markdown files in it
            for path in find_md_files(clonedir):
                with open(path, mode='r') as fd: # if it's a markdown file, open it in read mode
                    links += find_links(fd) # search for links
else:
    for directory in args.location:
        chdir(directory)
        for path in find_md_files(directory):
            with open(path, mode='r') as fd: # if it's a markdown file, open it in read mode
                links += find_links(fd) # search for links
for link in links:
    print("""
Link found: "{}"
URL: "{}"
Status: {}

in this line:
{}
""".format(link[0], link[1], check_link(link[1]), link[2]))
    print('-'*80)
