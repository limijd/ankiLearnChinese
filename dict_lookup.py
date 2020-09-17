#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=C0103,W0703,R1711

'''
dict_lookup.py is a separate command line tool to look up a character/word/idiom from dictionary.

The result will be printed on screen.

This script is not designed for quick lookup. It takes some time to load all the dictionaries.

'''

import os
import argparse
import logging
import MultiChineseDict

def main():
    """ program main entry """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(prog=os.path.basename(__file__)
            , description="dict_lookup.py: lookup word from dictionary")
    parser.add_argument('-d', '--debug', action='store_true', help="debug mode")
    parser.add_argument('word',  help='the word need to be looked up')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(format='[dict_lookup.py: %(asctime)s %(levelname)s] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)
    else:
        logging.basicConfig(format='[dict_lookup.py: %(asctime)s %(levelname)s] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', level=logging.ERROR)
    md = MultiChineseDict.MultiChineseDict()
    md.lookup(args.word).pp()
    return

if __name__ == "__main__":
    main()
