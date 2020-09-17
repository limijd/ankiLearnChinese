#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=C0103,W0703

"""
tlm_build.py

Build TLM model from YAML input file. This independent tool can just be used to check
if the YAML file complies TLM .

"""

import os
import argparse
import logging
import TextLessonModel

logging.getLogger("jieba").setLevel(logging.ERROR)
logging.basicConfig(format='[tlm_build.py: %(asctime)s %(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

parser: argparse.ArgumentParser = argparse.ArgumentParser(prog=os.path.basename(__file__)
        , description="tlm_build.py: TLM model check")
parser.add_argument("yaml_file", help='specify the yaml file')
args = parser.parse_args()

fn_yaml = args.yaml_file


tlm = TextLessonModel.TextLessonModel(fn_yaml)

print(tlm)
