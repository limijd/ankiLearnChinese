#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=C0103,W0703,R1711

'''
TTS service modules

GoogleTTS - TTS from google
XunfeiTTS - TTS from Xunfei (TBD)
AmazonPollyTTS - TTS from Amazon(TBD)
'''

import os
import logging
import html
from google.cloud import texttospeech

class GoogleTTS:
    """ Wrapper class to provide google TTS service """

    def __init__(self, config):
        self.config = config
        self.language_code = "cmn-CN"
        self.voice_name = "cmn-CN-Wavenet-A"
        self.speaking_rate = 1.0
        self.paragraph_break_time = "1s"

        if "GOOGLE_TTS_LANAGUAGE_CODE" in config:
            self.language_code = config["GOOGLE_TTS_LANAGUAGE_CODE"]

        if "GOOGLE_TTS_VOICE_NAME" in config:
            self.voice_name = config["GOOGLE_TTS_VOICE_NAME"]

        if "GOOGLE_TTS_SPEAKING_RATE" in config:
            self.speaking_rate = float(config["GOOGLE_TTS_SPEAKING_RATE"])

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(
                os.path.expanduser(config["GOOGLE_APPLICATION_CREDENTIALS"]))

        return

    @staticmethod
    def list_voices():
        """Lists the available voices."""
        client = texttospeech.TextToSpeechClient()
        voices = client.list_voices()
        for voice in voices.voices:
            print(f"Name: {voice.name}")
            for language_code in voice.language_codes:
                print(f"Supported language: {language_code}")
            ssml_gender = texttospeech.SsmlVoiceGender(voice.ssml_gender)
            print(f"SSML Voice Gender: {ssml_gender.name}")
            print(f"Natural Sample Rate Hertz: {voice.natural_sample_rate_hertz}\n")

    def text_to_ssml(self, inputfile):
        """
        auxiliary function to convert pure text to ssml .
        break time will be inserted for each paragraph
        """
        raw_lines = inputfile
        escaped_lines = html.escape(raw_lines)
        # Convert plaintext to SSML
        # Wait two seconds between each address
        ssml = "<speak>{}</speak>".format(
            escaped_lines.replace("\n", '\n<break time="%s"/>'%self.paragraph_break_time)
        )
        return ssml

    def synthesize_chinese_ssml(self, ssml_text, output):
        """ synthesize Chinese from SSML input """
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)

        voice = texttospeech.VoiceSelectionParams(
                language_code=self.language_code,
                name=self.voice_name,
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE)

        audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=self.speaking_rate)

        response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config)

        with open(output, "wb") as out:
            out.write(response.audio_content)
            logging.info('Audio content written to file %s', output)
        return

    def synthesize_chinese_text(self, content, output):
        """ synthesize Chinese from pure text input """
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=content)

        voice = texttospeech.VoiceSelectionParams(
                language_code=self.language_code,
                name=self.voice_name,
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE)

        audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=self.speaking_rate)

        response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config)

        # The response's audio_content is binary.
        with open(output, "wb") as out:
            out.write(response.audio_content)
            logging.info('Audio content written to file %s', output)
        return
