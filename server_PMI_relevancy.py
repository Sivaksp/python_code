#!/usr/bin/env python
# SCRIPT_NAME=server_PMI_relevancy.py
# SCRIPT_DESCRIPTION=Prints the relevant content of the CI
# SCRIPT_LANGUAGE=python 2.*
# SCRIPT_PLATFORM=linux

# Modules
import os
import sys
import requests
import argparse
from termcolor import colored

help_text = 'Helps in collecting the relevant PMI content of the server'

parser = argparse.ArgumentParser(
    description=help_text, usage='%(prog)s -s/-m ci/hostfile', epilog='Example: %(prog)s -s ns9596')
parser.add_argument('-s', '--single', dest='alone',
                    nargs='+', help='For Single Server')
parser.add_argument('-m', '--multi', dest='several',
                    nargs='+', help='For Multiple Servers')

if len(sys.argv) == 1:
    parser.print_help(sys.stderr)
    sys.exit(1)

args = parser.parse_args()

# Variables
#data = args.several[0]
try:
    data = args.several[0]
except TypeError:
    data = args.alone[0]

# Functions

def get_relevant(x):
    for line in x:
        print(line)

if args.several and os.path.isfile(data):
    with open(data, 'r') as list:
        for ci in list.readlines():
            ci = ci.strip()
            if ci:
                res = requests.get("https://pmi.int.thomsonreuters.com/api/v3/ci/{}/content/relevant".format(ci), headers={"Accept": "application/json"})
                out = res.json()
                if 'errors' in out:
                   text = colored("There is no information availabe for: {}".format(ci), 'red')
                   print(text)
                else:
                    text = colored("\nThe relevant content for {} is: ".format(ci), 'green', attrs=['bold'])
                    print(text)
                    get_relevant(out)
else:
    server = data.strip()
    if server:
        res = requests.get("https://pmi.int.thomsonreuters.com/api/v3/ci/{}/content/relevant".format(server), headers={"Accept": "application/json"})
        out = res.json()
        if 'errors' in out:
            text = colored("There is no information availabe for: {}".format(server), 'red')
            print(text)
        else:
            text = colored("\nThe relevant content for {} is: ".format(server), 'green', attrs=['bold'])
            print(text)
            get_relevant(out)
