#!/usr/bin/env python3 # -*- coding: utf-8 -*-
# pylint: disable=C0103,W0703

"""

Build TLM (TextLessonModel) from the input YAML file

The YAML file need to at least define "lesson", "tag" field. "tag" is better to be unique.
Otherwise the data in this model could eventually interfere with the data which has same tag.

The top level model is TextLessonModel.  TLM_Article, TLM_Grammar, TLM_WordList will be the
concret content in the model.

There are 3 TLM_Question_* classes.  TLM_Question_QA, TLM_Question_MCQ, TLM_Question_Cloze.
A TLM_Question* can belong to TLM_Article,TLM_Grammar, TLM_WordList, TextLessonModel


"""

import sys
import yaml
import logging
import re
import jieba
import html
from collections import OrderedDict
import Config

class TLM_Question_QA:
    """ represent a basic question-answer """
    def __init__(self, question, answer):
        return

    def __repr__(self):
        return

class TLM_Question_MCQ:
    """ represent a single/multiple choices question """
    def __init__(self, question, choices, answers):
        return

    def __repr__(self):
        return

class TLM_Question_Cloze:
    """ represent a cloze question """
    def __init__(self, raw_cloze, owner, tlm):
        self.raw_cloze = raw_cloze
        self.owner = owner #class object not str
        self.tlm = tlm
        pass

    def genAnki(self):
        cloze_unfilled = self.raw_cloze
        cloze_unfilled = re.sub(r"{.*?}", "{____}", cloze_unfilled, re.UNICODE)
        cloze_unfilled = re.sub(r"\t", "  ", cloze_unfilled, re.UNICODE)
        cloze_unfilled = re.sub(r"\n", "<br>", cloze_unfilled, re.UNICODE)

        cloze_filled = re.sub(r"\t", "  ", self.raw_cloze, re.UNICODE)
        cloze_filled = re.sub(r"\n", "<br>", cloze_filled, re.UNICODE)
        cloze_filled = re.sub(r"{", r"{<b>", cloze_filled, flags=re.UNICODE)
        cloze_filled = re.sub(r"}", r"</b>}", cloze_filled, flags=re.UNICODE)

        cloze_hint = self.owner.getHint()
        cloze_fullHint = self.owner.genFullHintAnkiField()

        anki_row = "\t".join([cloze_filled, cloze_unfilled, cloze_hint,
                              cloze_fullHint, self.tlm.tag])
        return anki_row

class TLM_Grammar:
    def __init__(self, grammar, raw_grammar, tlm):
        self.tlm = tlm
        self.grammar = grammar
        self.raw_data = raw_grammar
        self.clozes = []
        self.genQuestions()
        pass

    def genFullHintAnkiField(self):
        ret = "<b>语法: %s</b><br>"%self.grammar
        if "clozes" in self.raw_data:
            clozes = "<br>".join(self.raw_data["clozes"])
            clozes = re.sub(r"\n", r"<br>", clozes, flags=re.UNICODE)
            ret = ret + clozes
        return ret


    def getHint(self):
        return "语法: %s"%self.grammar

    def genQuestions(self):
        if not "clozes" in self.raw_data:
            return []

        for clz in self.raw_data["clozes"]:
            cloze = TLM_Question_Cloze(clz, self, self.tlm)
            self.clozes.append(cloze)
            cloze.genAnki()

class TLM_Article:
    """ represent a Text/Essay/Article """

    def __init__(self, raw_article, tlm):
        self.tlm = tlm
        self.clozes = []
        self.raw_data = raw_article
        if not "title" in raw_article:
            logging.error("Article must have \"title\" field")
            print(raw_article)
            sys.exit(1)
        self.title = raw_article["title"]
        if not self.title or len(self.title)==0:
            logging.error("Title can't be none")
            sys.exit(1)
        self.paragraphs = None
        if not "paragraphs" in raw_article:
            logging.error("Article model must contain paragraphs")
            sys.exit(1)
        if isinstance(raw_article["paragraphs"], list):
            self.paragraphs = raw_article["paragraphs"]
        elif isinstance(raw_article["paragraphs"], str):
            self.paragraphs = [raw_article["paragraphs"]]
        else:
            assert 0
        self.type = "文" #[文, 诗，词，歌]
        if "type" in raw_article:
            self.type = raw_article["type"]
            types = "[文, 古诗，词，诗歌, 笑话, 儿歌, 童话, 神话, 谜语, 幽默, 寓言]"
            if not self.type in  types:
                logging.error("type must be: %s, current type: %s", types, self.type)
                sys.exit(1)

        self.sentences = []
        self.words = []
        self.wordToSentences = {}

        self.genSentences()
        self.genWordlist()

        self.genQuestions()

        return

    def genQuestions(self):
        if not "clozes" in self.raw_data:
            return []

        for clz in self.raw_data["clozes"]:
            cloze = TLM_Question_Cloze(clz, self, self.tlm)
            self.clozes.append(cloze)
            cloze.genAnki()

    def genSentences(self):
        self.sentences = []
        for paragraph in self.paragraphs:
            paragraph = paragraph.strip()
            #paragraph = re.sub("\n", "", paragraph)
            for s in re.finditer(r".*?[\r\n。!？；][\"”]*", paragraph, re.UNICODE):
                if len(s.group(0).strip()) == 0:
                    continue
                s = s.group(0).strip()
                s = re.sub(r"\n", "", s)
                s = re.sub(r",", "，", s)
                s = re.sub(r"^[0-9]\.", "", s)
                self.sentences.append(s)

        return

    def getHint(self):
        return "课文: %s"%self.title

    def genFullHintAnkiField(self):
        ret = "<b>课文: %s</b><br>"%self.title
        if "clozes" in self.raw_data:
            clozes = "<br>".join(self.raw_data["clozes"])
            clozes = re.sub(r"\n", r"<br>", clozes, flags=re.UNICODE)
            ret = ret + clozes
        return ret

    def genWordlist(self):
        for sentence in self.sentences:
            for tok in jieba.cut(sentence, cut_all=False):
                if re.search(r"[   :!！\b\n\r\t.\"‘“”。，\]\[]", tok, re.UNICODE):
                    continue
                self.words.append(tok)
                if tok in self.wordToSentences:
                    ss = self.wordToSentences[tok]
                    ss[sentence] = True
                else:
                    self.wordToSentences[tok] = {sentence:True}
        return

    def generateSSML(self):
        paragraphs = "\n".join(self.paragraphs)
        article = "%s\n\n%s"%(self.title, paragraphs)
        article = html.escape(article)
        ssml = "<speak>{}</speak>".format(article.replace("\n", '\n<break time="%s"/>'%self.tlm.paragraph_break_time))
        return ssml

    def getUniqueName(self):
        return "%s.%s"%(self.tlm.text["tag"], self.title)

    def __repr__(self):
        s = "[Article]:《%s》, " % self.title
        s = s + "%d paragraphs, %d sentences, %d words"%(len(self.paragraphs), len(self.sentences), len(self.words))
        return s

class TLM_WordList:
    def __init__(self, wordlist):
        self.word_list = wordlist

    def addWord(self, word):
        if not word in self.word_list:
            self.word_list.append(word)
        return

class TextLessonModel:
    def __init__(self, fn):
        logging.info("Building text model from: %s", fn)
        self.fn = fn
        self.orig_doc = self.load_yaml(fn)
        assert self.orig_doc

        self.config = Config.LoadConfig()
        self.paragraph_break_time = "1s"
        if "GOOGLE_TTS_PARAGRAPH_BREAK_TIME" in self.config:
            self.paragraph_break_time = self.config["GOOGLE_TTS_PARAGRAPH_BREAK_TIME"]

        self.text = {}
        self.text["lesson"] = self.orig_doc["lesson"]
        self.lesson = self.text["lesson"]
        self.text["tag"] = self.orig_doc["tag"]
        self.tag = self.text["tag"]
        self.text["articles"] = self.orig_doc["articles"]
        if "grammars" in self.orig_doc:
            self.text["grammars"] = self.orig_doc["grammars"]
        else:
            self.text["grammars"] = []

        if "words" in self.orig_doc:
            self.text["words"] = self.orig_doc["words"]
        else:
            self.text["words"] = []

        self.articleModels = OrderedDict()
        self.grammarModels = OrderedDict()
        self.wordsModel = {}
        if "words" in self.orig_doc:
            for line in self.orig_doc["words"]:
                line = line.strip()
                words = re.sub(r"\n", " ", line, re.UNICODE)
                words = words.split()
                for w in words:
                    if w == "":
                        continue
                    self.wordsModel[w] = True

        for article in self.text["articles"]:
            title = article["title"]
            tm = TLM_Article(article, self)
            self.articleModels[title] = tm

        for grammar in self.text["grammars"]:
            gm = TLM_Grammar(grammar["grammar"], grammar, self)
            self.grammarModels[grammar["grammar"]] = gm

    def __repr__(self):
        s = "lesson: %s\n" % self.text["lesson"]
        s = s + "tag: %s\n" % self.text["tag"]
        s = s + "Articles: \n"
        for am in self.articleModels.values():
            s = s + "\t" + am.__repr__() + "\n"

        if self.text["words"]: 
            s = s + "Words: \n"
            s = s + "\t" + ",".join(self.text["words"])

        return s

    def load_yaml(self, fn):
        orig_doc = None
        if not fn.endswith(".yaml"):
            logging.error("Text model can only be built based on YAML data")
            sys.exit(1)
        fp = open(fn, "r")
        orig_doc = yaml.full_load(fp)
        return orig_doc

if __name__ == "__main__":
    tlm = TextLessonModel("./examples/tlm_example.yaml")
    print(tlm)
