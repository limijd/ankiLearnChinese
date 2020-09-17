#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=C0103,W0703,R0902,R1711,C0116,C0115

'''
Load Config.yaml

'''
import os
import sys
import logging
import json
import yaml

SCRIPT_PATH=os.path.dirname(os.path.realpath(__file__))

def LoadConfig():
    fn = "%s/Config.yaml"%SCRIPT_PATH
    logging.info("Loading config file from: %s", fn)
    if not os.path.exists(fn):
        logging.error("Config file doesn't exist: %s", fn)
        sys.exit(1)

    fp = open(fn, "r")
    config = yaml.full_load(fp)
    fp.close()

    logging.debug("YAML config: \n%s", json.dumps(config, indent=4))
    return config
