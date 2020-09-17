#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=C0103,W0703

"""
yaml_check.py

Check if there is syntax error in YAML file. If it's good, do a pretty printing in JSON format.

"""

import sys
import os
import argparse
import json
import yaml


parser: argparse.ArgumentParser = argparse.ArgumentParser(prog=os.path.basename(__file__)
        , description="yaml_check.py: YAML syntax check")
parser.add_argument("yaml_file", help='specify the yaml file')
args = parser.parse_args()

fn_yaml = args.yaml_file

fp_yaml= open(fn_yaml, "r")

try:
    doc=yaml.full_load(fp_yaml)
except yaml.parser.ParserError as e:
    print("YAML file syntax error: %s"%fn_yaml)
    print(e)
    sys.exit(-1)

json.dump(doc, sys.stdout, indent=4, ensure_ascii=False)

print("\n\n==== Syntax of this YAML is good! ====\n")
