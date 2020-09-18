#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=C0103,W0703,R0902,R1711,R0912,R0914,R0911

"""
ANKI Learn Chinese  - alc.py
"""

import os
import sys
import re
import argparse
import logging
from collections import OrderedDict
import jieba
from MultiChineseDict import MultiChineseDict
from TextLessonModel import TextLessonModel
from TTSService import GoogleTTS

import Config

logging.getLogger("jieba").setLevel(logging.ERROR)
SCRIPT_PATH=os.path.dirname(os.path.realpath(__file__))

class AnkiLearnChineseNotes:
    """ main class to process content and produce different kinds of ANKI notes"""

    def __init__(self, tlm=None, args=None, md=None):
        self.config = Config.LoadConfig()
        self.args = args
        self.tlm = tlm #Yaml Lesson Model object
        self.note_type_fields = self.config["ANKI_CHINESE_WORD_NOTE_TYPE"]
        self.word_list = {}
        self.char_list = {}
        self.idiom_list = {}
        self.ignored_chars = {}

        self.enable_tts = self.config["GOOGLE_TTS_ENABLE"]
        self.tts_output_dir = self.config["TTS_OUTPUT_DIR"]
        self.tts_output_dir = os.path.expanduser(self.config["TTS_OUTPUT_DIR"])
        if not self.tts_output_dir.startswith("/"):
            self.tts_output_dir = "%s/%s"%(SCRIPT_PATH, self.tts_output_dir)
        if args.with_tts:
            if self.enable_tts:
                logging.info("TTS is enabled, output database is available: %s",
                             self.tts_output_dir)
            else:
                logging.info("TTS is not-enabled, please config Google TTS in Config.yaml")
                sys.exit(1)
        if not os.path.exists(self.tts_output_dir):
            logging.error("TTS output folder doesn't exist: %s", self.tts_output_dir)

        self.tts_service = GoogleTTS(self.config)
        assert os.path.exists(self.tts_output_dir)

        self.not_found_word_list = {}
        self.tags = None
        self.gen_list = False
        self.with_tts = False

        #self.ignore_lst_fn = "%s/dicts/alc.ignore.lst"%SCRIPT_PATH
        self.ignore_lst = {}
        #for l in open(self.ignore_lst_fn, "r").readlines():
        #    l = l.strip()
        #    self.ignore_lst[l] = True

        self.all_word_to_sentence = {}
        self.all_sentences_count = {}
        self.genArticle = True

        if not md:
            self.md = MultiChineseDict()
        else:
            self.md = md

        return

    def setGenArticle(self):
        """ set whether to generate article notes or not """
        self.genArticle = True

    def setWordToSentenceDict(self, d):
        """ set the dictionary that lookup sentence from a word """
        self.all_word_to_sentence = d

    def fixWordToSentenceDict(self):
        """ fix word to sentence dict """
        worklist = []
        for ch, dummy in self.char_list.items():
            if not ch in self.all_word_to_sentence:
                worklist.append(ch)

        for word, dummy in self.word_list.items():
            cw = self.md.allWords[word]
            if not cw.raw_js["explanation"] and not cw.raw_js["x7explanation"]:
                continue
            if not word in self.all_word_to_sentence:
                worklist.append(word)

        for idiom, dummy in self.idiom_list.items():
            if not idiom in self.all_word_to_sentence:
                worklist.append(idiom)

        worklist = set(worklist)
        values = list(self.all_word_to_sentence.values())
        for word in worklist:
            for sd in values:
                for s in sd.keys():
                    if s.find(word) != -1:
                        if word in self.all_word_to_sentence:
                            d = self.all_word_to_sentence[word]
                            d[s] = 0
                        else:
                            self.all_word_to_sentence[word] = {s:0}
        return

    def setWithTTS(self, with_tts):
        """ whether generate tts for notes """
        self.with_tts = with_tts

    def setGenList(self, fn):
        """ whether to dump the word list to the given file """
        self.gen_list = fn

    def sortFuncForSentenceCount(self, x):
        """ sort function to make sure low hit sentences are first """
        if not x in self.all_sentences_count:
            return 0

        return self.all_sentences_count[x]

    def getExampleSentence(self, word):
        """
            fetch one example sentence. It tend to pick up the one has not been
            picked up.
        """
        if not word in self.all_word_to_sentence:
            return ""

        sentences = self.all_word_to_sentence[word]
        keys = list(sentences.keys())
        keys.sort(key=self.sortFuncForSentenceCount, reverse=False)
        ret = keys[0]

        if ret in self.all_sentences_count:
            count = self.all_sentences_count[ret]
            self.all_sentences_count[ret] = count + 1
        else:
            self.all_sentences_count[ret] = 1

        return ret

    def get_ch_fields(self, ch):
        """ produce word note fields for a Chinese character """
        cc = self.md.allChars[ch]
        r = OrderedDict()
        expl = cc.raw_js["explanation"]

        if cc.raw_js["x7explanation"]:
            expl = cc.raw_js["x7explanation"]
            expl = MultiChineseDict.prettyX7Explanation(expl)
        else:
            if expl:
                expl = expl.replace("\r", "<br>")
                expl = expl.replace("\n", "<br>")

        if expl:
            expl.replace(ch, "～")
        else:
            expl = ""

        pinyin = cc.raw_js["pinyin"]
        if isinstance(pinyin, list):
            pinyin = ", ".join(pinyin)

        r["字词"] = ch
        r["拼音"] = pinyin
        if not "strokes" in cc.raw_js or not cc.raw_js["strokes"]:
            r["笔画"] = ""
        else:
            r["笔画"] = cc.raw_js["strokes"]
        words = " ".join(map(lambda x:x.word, cc.words[:5]))
        r["词组"] = words
        r["去字词组"] = words.replace(ch, "__")
        idioms = " ".join(map(lambda x:x.idiom, cc.idioms[:5]))
        r["成语"] = idioms
        r["去字成语"] = idioms.replace(ch, "__")
        r["标准解释"] = expl
        r["字词频"] = "%d"%cc.freq
        ex = self.getExampleSentence(ch)
        ex = re.sub(ch, "～", ex, re.UNICODE)
        r["例句"] = ex
        r["辅助_修改读音"] = ""
        r["辅助_修改读音"] = "[sound:%s.mp3]"%ch

        assert list(r.keys()) == self.config["ANKI_CHINESE_WORD_NOTE_TYPE"]

        if self.tags:
            r["tags"] = self.tags
        return r

    def get_word_fields(self, word):
        """ produce word note fields for a Chinese word """
        cw = self.md.allWords[word]
        r = OrderedDict()
        expl = cw.raw_js["explanation"]

        pinyin = []
        if cw.raw_js["x7explanation"]:
            x7expl = cw.raw_js["x7explanation"]
            expl = MultiChineseDict.prettyX7Explanation(x7expl)
            for x in x7expl:
                p = x[2]
                if p:
                    pinyin.append("%s"%p)
        else:
            if expl:
                expl = expl.replace("\r", "<br>")
                expl = expl.replace("\n", "<br>")

        if expl:
            expl.replace(word, "～")
        else:
            expl =""

        if not pinyin:
            pinyin = ""

        r["字词"] = word
        r["拼音"] = ", ".join(pinyin)
        r["笔画"] = ""
        r["词组"] = ""
        r["去字词组"] = ""
        r["成语"] = ""
        r["去字成语"] = ""
        r["标准解释"] = expl
        r["字词频"] = "%d"%cw.freq
        ex = self.getExampleSentence(word)
        ex = re.sub(word, "～", ex, re.UNICODE)
        r["例句"] = ex
        r["辅助_修改读音"] = "[sound:%s.mp3]"%word

        assert list(r.keys()) == self.config["ANKI_CHINESE_WORD_NOTE_TYPE"]

        if self.tags:
            r["tags"] = self.tags
        return r

    def get_idiom_fields(self, idiom):
        """ produce word note fields for a Chinese idom"""
        idm = self.md.allIdioms[idiom]
        r = OrderedDict()
        expl = idm.raw_js["explanation"]

        pinyin = idm.raw_js["pinyin"]
        if idm.raw_js["x7explanation"]:
            x7expl = idm.raw_js["x7explanation"]
            expl = MultiChineseDict.prettyX7Explanation(x7expl)
            if not pinyin:
                for x in x7expl:
                    p = x[2]
                    if p:
                        pinyin.append("%s"%p)
        else:
            if expl:
                expl = expl.replace("\r", "<br>")
                expl = expl.replace("\n", "<br>")

        if expl:
            expl.replace(idiom, "～")
        else:
            expl =""

        if not pinyin:
            pinyin = ""

        r["字词"] = idiom
        r["拼音"] = ", ".join(pinyin)
        r["笔画"] = ""
        r["词组"] = ""
        r["去字词组"] = ""
        r["成语"] = ""
        r["去字成语"] = ""
        r["标准解释"] = expl
        r["字词频"] = "%d"%idm.freq
        ex = self.getExampleSentence(idiom)
        ex = re.sub(idiom, "～", ex, re.UNICODE)
        r["例句"] = ex
        r["辅助_修改读音"] = "[sound:%s.mp3]"%idiom

        assert list(r.keys()) == self.config["ANKI_CHINESE_WORD_NOTE_TYPE"]

        if self.tags:
            r["tags"] = self.tags
        return r

    def handleNotFoundWords(self):
        """ if a word can't be found in dict, break it down to characters """
        handled_chars = {}
        for word, dummy in self.word_list.items():
            for ch in list(word):
                handled_chars[ch] = True

        not_found_chars = {}
        for w, dummy in self.not_found_word_list.items():
            for ch in list(w):
                if not ch in handled_chars:
                    not_found_chars[ch] = True

        for ch, dummy in not_found_chars.items():
            if ch in self.md.allChars:
                self.char_list[ch] = True
            else:
                self.ignored_chars[ch] = True

    def produceTTSOutput(self, word, just_check=None):
        """ use TTS to produce audio of the word """
        assert len(word)<100
        fn = "%s.mp3"%word
        fn_abs = "%s/%s"%(self.tts_output_dir, fn)
        if os.path.exists(fn_abs):
            return False

        #use google tts
        if not just_check:
            self.tts_service.synthesize_chinese_text(word, fn_abs)
        return True

    def genAnkiImportTxt(self, fn, fn_articles=None, fn_clozes=None):
        """ generate all notes to files ready to be imported by ANKI """
        genlist = []

        self.handleNotFoundWords()
        if len(self.ignored_chars) > 0:
            logging.info("忽略%d个无法查找到的汉字: %s",
                         len(self.ignored_chars),
                         " ".join(self.ignored_chars.keys()))

        self.fixWordToSentenceDict()

        fp = sys.stdout

        if fn:
            fp = open(fn, "w")

        for ch, dummy in self.char_list.items():
            genlist.append(self.md.allChars[ch])
            chs = self.get_ch_fields(ch)
            values = []
            for dummy, fld in chs.items():
                if ch:
                    assert isinstance(fld, str)
                    values.append(fld)
                else:
                    values.append("")
            fp.write("\t".join(values))
            fp.write("\n")

        ignore_words_without_explanation = []
        for word, dummy in self.word_list.items():
            cw = self.md.allWords[word]
            if not cw.raw_js["explanation"] and not cw.raw_js["x7explanation"]:
                ignore_words_without_explanation.append(word)
                continue
            genlist.append(self.md.allWords[word])
            fp.write("\t".join(self.get_word_fields(word).values()))
            fp.write("\n")

        logging.info("Ignore %d words without explanation: %s",
                len(ignore_words_without_explanation), " ".join(ignore_words_without_explanation))

        for idiom, dummy in self.idiom_list.items():
            genlist.append(self.md.allIdioms[idiom])
            fp.write("\t".join(self.get_idiom_fields(idiom).values()))
            fp.write("\n")

        if fn:
            fp.close()

        if self.gen_list:
            fp = open(self.gen_list, "w")
            for x in genlist:
                fp.write("%d %s\n" %(x.freq, x.getName()))
            fp.close()

        if self.with_tts:
            words_to_tts = []
            for x in genlist:
                if self.produceTTSOutput(x.getName(), just_check=True):
                    words_to_tts.append(x.getName())
            logging.info("producing tts audios for %d new words...", len(words_to_tts))
            for x in words_to_tts:
                self.produceTTSOutput(x)

        if fn_articles:
            self.GenArticles(fn_articles)

        if fn_clozes:
            self.GenClozes(fn_clozes)
        return

    def GenClozes(self, fn_clozes):
        """ generate cloze note to clozes file """
        logging.info("Genearting clozes to: %s", fn_clozes)
        clozes = []
        for dummy, obj in self.tlm.grammarModels.items():
            for cloze in obj.clozes:
                clozes.append(cloze)

        fp = open(fn_clozes, "w")
        for cloze in clozes:
            fp.write(cloze.genAnki())
            fp.write("\n")
        fp.close()
        return

    def GenArticles(self, fn_articles):
        """ generate article notes to article file """
        if not self.genArticle:
            return

        logging.info("Generate article import file and article TTS to: %s", fn_articles)

        fp = open(fn_articles, "w")
        for title, am in self.tlm.articleModels.items():
            r = OrderedDict()
            r["uniqTitle"] = "%s.%s"%(self.tlm.lesson, title)
            r["title"] = title
            ss = ""
            for s in am.paragraphs:
                for line in s.split("\n"):
                    line = line.strip()
                    if line=="":
                        continue
                    line = re.sub("\t", "  ", line, re.UNICODE) # make sure no tab.
                    ss = ss +  "<p>%s</p>"%line
                ss = ss + "<br>"
            r["paragraphs"] = ss

            audio_fn = "%s.%s.mp3"%(self.tlm.lesson, title)
            ssml_fn = "%s/%s.%s.ssml"%(self.tts_output_dir, self.tlm.lesson, title)
            ssml = am.generateSSML()
            fn_abs = "%s/%s"%(self.tts_output_dir, audio_fn)
            if not os.path.exists(fn_abs):
                logging.info("generate tts audio to: %s", audio_fn)
                if self.args.keep_ssml:
                    print("keep ssml: %s"%ssml_fn)
                    fp_ssml = open(ssml_fn, "w")
                    fp_ssml.write(ssml)
                    fp_ssml.close()
                self.tts_service.synthesize_chinese_ssml(ssml, fn_abs)
            r["tts"] = "[sound:%s]"%audio_fn
            r["tag"] = self.tlm.tag
            fp.write("\t".join(r.values()))
            fp.write("\n")
        fp.close()

        return

    def addWord(self, word):
        """ add a word to the input word list """
        if len(word) == 1:
            self.char_list[word] = True
        else:
            if word in self.md.allIdioms:
                self.idiom_list[word]=True
            else:
                self.word_list[word] = True
        return


    def lookupWord(self, word):
        """ check whether the word is in any dictionary """
        if len(word) == 1:
            if word in self.md.allChars:
                return True
            return False

        if word in self.md.allIdioms:
            return True

        if word in self.md.allWords:
            #the word comes from frequency list. But no item in dictionary
            w = self.md.allWords[word]
            if not w.raw_js["explanation"] and not w.raw_js["x7explanation"]:
                return False
            #the word is to rare, make it learn as character
            if word in self.ignore_lst:
                return False
            return True

        return False

    def processWordList(self, word_list, extend_ch=None, ecfl=None):
        """ process input word list"""
        logging.debug("processing word list: %s", word_list)
        for word in word_list:
            if not self.lookupWord(word):
                if len(word)>2:
                    for tok in jieba.cut(word, cut_all=True):
                        if self.lookupWord(tok):
                            self.addWord(tok)
                        else:
                            self.not_found_word_list[tok] = True
                else:
                    self.not_found_word_list[word] = True
            else:
                self.addWord(word)

        if extend_ch:
            for ch in self.char_list:
                cc = self.md.allChars[ch]
                for cw in cc.words[:extend_ch]:
                    if ecfl and cw.freq>ecfl: #only
                        continue
                    if not cw.word in self.word_list and not cw.word in self.idiom_list:
                        assert len(cw.word) > 1
                        self.addWord(cw.word)

        return

def GenAnkiFromString(s, args):
    """
        generate ANKI notes from a given string
        for such case, only Word note type will be generated
    """
    alc_notes = AnkiLearnChineseNotes()
    alc_notes.setWithTTS(args.with_tts)
    alc_notes.processWordList(list(jieba.cut(s, cut_all=False)),
            args.extend_char, args.extend_freq_limit)
    if args.gen_list:
        alc_notes.setGenList(args.gen_list)
    if args.tags:
        alc_notes.tags = args.tags
    alc_notes.genAnkiImportTxt(args.output)

def GenAnkiFromTextFile(fn, args):
    """
        generate ANKI notes from a given text file
        for such case, only Word note type will be generated
    """
    alc_notes = AnkiLearnChineseNotes(args=args)
    alc_notes.setWithTTS(args.with_tts)
    fp = open(fn,"r")
    for line in fp.readlines():
        line = line.strip()
        alc_notes.processWordList(list(jieba.cut(line, cut_all=False)),
                args.extend_char, args.extend_freq_limit)
    if args.gen_list:
        alc_notes.setGenList(args.gen_list)
    if args.tags:
        alc_notes.tags = args.tags
    alc_notes.genAnkiImportTxt(args.output)

def GenAnkiFromOneYamlTLM(args, yaml_fn, md):
    """
        generate ANKI notes from a given YAML TLM file
        for such case, all kinds of notes will be genearted based on
        content in TLM model.
    """
    tlm = TextLessonModel(yaml_fn)
    all_sentences = {}
    all_words = {}
    all_word_to_sentence = {}
    for am in tlm.articleModels.values():
        for s in am.sentences:
            all_sentences[s] = True
        for w in am.words:
            all_words[w] = True
        for x,y in am.wordToSentences.items():
            if not x in all_word_to_sentence:
                all_word_to_sentence[x] = {}
            for s in y.keys():
                all_word_to_sentence[x][s] = 0

    words = list(all_words.keys())
    words.sort(key=lambda x: len(all_word_to_sentence[x]))

    alc_notes = AnkiLearnChineseNotes(tlm, args=args, md=md)
    alc_notes.setWithTTS(args.with_tts)
    alc_notes.setWordToSentenceDict(all_word_to_sentence)
    alc_notes.processWordList(words, extend_ch=None, ecfl=None)
    if args.gen_list:
        alc_notes.setGenList(args.gen_list)
    if args.tags:
        alc_notes.tags = args.tags
    else:
        alc_notes.tags = tlm.tag

    fn = yaml_fn
    fn = re.sub(".yaml$", "", fn)
    output_words="%s.anki.import.txt"%fn
    output_articles = "%s.anki.import.articles.txt"%fn
    output_clozes = "%s.anki.import.clozes.txt"%fn

    print(output_words, output_articles, output_clozes)
    alc_notes.setGenArticle()
    alc_notes.genAnkiImportTxt(output_words, output_articles, output_clozes)

    return

def GenAnkiFromAllYamlTLM(args):
    """ genearte ANKI notes from all YAML files"""
    logging.info("processing YAML lesson model for all YAML files...")
    logging.info("-output is ignored when YAML TLM file is input.")
    md = MultiChineseDict()
    for yaml_fn in args.input_yaml_tlm:
        GenAnkiFromOneYamlTLM(args, yaml_fn, md)
    return

def cli(args):
    """ entry of program CLI """
    if args.tags:
        if not args.tags.startswith("#"):
            logging.error("Suggest use #<something> as tag name for better orgnization")
            sys.exit(1)

    if args.input_string:
        GenAnkiFromString(args.input_string, args)

    if args.input_text:
        GenAnkiFromTextFile(args.input_text, args)

    if args.input_yaml_tlm:
        GenAnkiFromAllYamlTLM(args)

    return

def main():
    """ entry of program """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(prog=os.path.basename(__file__)
            , description="alc: Anki Learn Chinese ")
    parser.add_argument('-d', '--debug', action='store_true', help="debug mode")
    parser.add_argument('-is', '--input_string',
            help="Generate ANKI notes for words extracted from the string")
    parser.add_argument('-it', '--input_text',
            help="Genearte ANKI notes for words extracted from the text file")
    parser.add_argument('-iyt', '--input_yaml_tlm', nargs='+',
            help="Generate ANKI notes for TLM model from the  yaml file")
    parser.add_argument('-ks', '--keep_ssml', action='store_true', default=True,
            help="keep ssml when do tts")
    parser.add_argument('-ec', '--extend_char', type=int,
            help="Put N high frequency words/idioms that uses the char into word list")
    parser.add_argument('-ecfl', '--extend_freq_limit', type=int,
            help="only extend with words that has high freqency than the limit")
    parser.add_argument('-gl', '--gen_list',
            help="dump the word list to specified file")
    parser.add_argument('-t', '--tags',
            help="add tags when create ANKI import file")
    parser.add_argument('-wt', '--with_tts', action='store_true', default=True,
            help="generate tts audio, default is True")
    parser.add_argument('-o', '--output',
            help='specify the output file')
    parser.set_defaults(func=cli)

    args = parser.parse_args()
    try:
        args.func
    except AttributeError:
        parser.error("too few arguments")

    if args.debug:
        logging.basicConfig(format='[alc: %(asctime)s %(levelname)s] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)
    else:
        logging.basicConfig(format='[alc: %(asctime)s %(levelname)s] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)
    args.func(args)

if __name__ == "__main__":
    main()
