#!/usr/bin/env python3
from subprocess import run, PIPE
from os import chdir, walk
from tempfile import TemporaryDirectory
from shutil import rmtree
from argparse import ArgumentParser
parser = ArgumentParser('md-link-linter')
parser.add_argument('-g', '--git', action='store_true', help="lint a git repository instead of a directory")
parser.add_argument('-f', '--filter', action='store_true', help="filter only broken links to output")
parser.add_argument('location', nargs='+', help="the directories (or repository urls if --git) to lint")
args = parser.parse_args()
def read_until(text, stop):
    snippet = ''
    for char in text:
        if char == stop:
            return snippet
        snippet += char
def scan(fd):
    fd.seek(0)
    i = 0
    char = fd.read(1)
    while char:
        if char in ('\n', '[', ']'):
            yield char, i
        char = fd.read(1)
        i += 1
def find_links(fd):
    fd.seek(0)
    text = fd.read()
    lines = [0]
    pairs = []
    for lead in scan(fd):
        if lead[0] == '\n':
            lines.append(lead[1])
        elif lead[0] == '[':
            pairs.append([lead[1]])
        elif lead[0] == ']':
            for i, pair in reversed(tuple(enumerate(pairs))):
                if len(pair) == 1:
                    pairs[i].append(lead[1])
                    break
    for pair in pairs:
        if len(pair) == 1:
            pairs.remove(pair)
    for start, end in pairs:
        if text[end+1] != '(':
            continue
        for i, line in reversed(tuple(enumerate(lines))):
            if line <= start:
                yield text[start+1:end], read_until(text[end+2:], ')'), text[line:lines[i+1]]
                break
def check_link(link):
    return eval(run(['curl', '-L', '-s', '-o /dev/null', '-m 5', '-w "%{http_code}"', link], stdout=PIPE).stdout)
def find_md_files(directory):
    for dirname, dirs, files in walk(directory): # explores the directory tree
        for entry in files:
            if entry.endswith('.md'):
                yield dirname+'/'+entry
for place in args.location:
    if args.git:
        with TemporaryDirectory() as clonedir: # create a temporary directory to clone the git repo into
            chdir(clonedir)
            run(['git','clone','-q',place,'.'],check=True) # clone the repo into the current directory
            rmtree('.git') # remove the .git folder so that we don't have to look for markdown files in it
            files = find_md_files(clonedir)
    else:
        files = find_md_files(place)
    for path in files:
        links = []
        with open(path) as fd: # if it's a markdown file, open it in read mode
            links += find_links(fd) # search for links
        for link in links:
            status = check_link(link[1])
            if args.filter and status.startswith('2'):
                continue
            print("""
Link found in file:
{}
Text: "{}"
URL: "{}"
Status: {}

in this line:
{}
""".format(path, link[0], link[1], status, link[2]))
            print('-'*80)
