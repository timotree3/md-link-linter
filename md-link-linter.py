#!/bin/env python3
import os
import tempfile
import shutil
import argparse
parser = argparse.ArgumentParser('md-link-linter')
parser.add_argument('repo', help="the git repository to lint")
args = parser.parse_args()
links = []
def find_links(fd):
    import re
    link_pattern = re.compile(r'\[([^!][^]]+)\]\((https?://[^\)]+)\)') # regex for an http link. made a small tweak to fix image finds breaking it.
    return link_pattern.findall(fd.read()) # returns a list of matches. each match is a tuple of the form: (linktext, linkurl)
with tempfile.TemporaryDirectory() as clonedir: # create a temporary directory to clone the git repo into
    os.chdir(clonedir)
    os.system('git clone -q ' + args.repo + ' .') # clone the repo into the current directory
    shutil.rmtree('.git') # remove the .git folder so that we don't have to look for markdown files in it
    for dirname, dirs, files in os.walk('.'): # explores the directory tree
        for entry in files:
            if entry.endswith('.md'):
                with open(dirname+'/'+entry, mode='r') as fd: # if it's a markdown file, open it in read mode
                    links += find_links(fd) # search for links
for link in links:
    print("\n{0[0]}: {0[1]} | Status: [ADDME]".format(link))
