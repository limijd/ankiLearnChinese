#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=C0103,W0703,R1711

'''
tts_google.py is a separate command line tool to generate voices from text based on Google
"Text-To-Speech service"
'''

import os
import sys
import argparse
import logging
import Config
from TTSService import GoogleTTS

SCRIPT_PATH=os.path.dirname(os.path.realpath(__file__))

def cli(args, config):
    """ Command Line Interface entry """
    content = None

    tts = GoogleTTS(config)

    if args.input_file:
        logging.info('Processing Chinese input file: %s', args.input_file)
        fp = open(args.input_file, "r")
        content = fp.read()
        fp.close()
        tts.synthesize_chinese_text(content, args.output)
    elif args.input_str:
        logging.info('Processing Chinese input string: %s', args.input_str)
        content = args.input_str
        tts.synthesize_chinese_text(content, args.output)
    elif args.input_file_ssml:
        logging.info('Processing ssml input file: %s', args.input_file_ssml)
        fp = open(args.input_file_ssml, "r")
        content = fp.read()
        fp.close()
        tts.synthesize_chinese_ssml(content, args.output)
    else:
        logging.error("No input to process")
        sys.exit(1)

    return


def main():
    """ program main entry """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(prog=os.path.basename(__file__)
            , description="google_ch_tts.py: TTS based on google API")
    parser.add_argument('-d', '--debug', action='store_true', help="debug mode")
    parser.add_argument('-if', '--input_file', help='specify the input file')
    parser.add_argument('-ifs', '--input_file_ssml', help='specify the ssml input file')
    parser.add_argument('-is', '--input_str', help='specify the input string')
    parser.add_argument('-o', '--output', type=str, default="output.mp3",
                        help='specify the output file, default is "output.mp3" ')
    parser.set_defaults(func=cli)

    args = parser.parse_args()
    try:
        args.func
    except AttributeError:
        parser.error("too few arguments")

    if args.debug:
        logging.basicConfig(format='[tts_google.py: %(asctime)s %(levelname)s] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)
    else:
        logging.basicConfig(format='[tts_google.py: %(asctime)s %(levelname)s] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

    config = Config.LoadConfig()
    if not "GOOGLE_APPLICATION_CREDENTIALS" in config:
        logging.error("GOOGLE_APPLICATION_CREDENTIALS must be set in config file")
        sys.exit(1)

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(
            os.path.expanduser(config["GOOGLE_APPLICATION_CREDENTIALS"]))

    args.func(args, config)

if __name__ == "__main__":
    main()
