#!/usr/bin/env python3 # -*- coding: utf-8 -*-
# pylint: disable=C0103,W0703

"""

Build TLM (TextLessonModel) from the input YAML file

The YAML file need to at least define "lesson", "tag" field. "tag" is better to be unique.
Otherwise the data in this model could eventually interfere with the data which has same tag.

The top level model is TextLessonModel.  TLM_Article, TLM_Grammar will be the
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

class TLM_Question:
    def __init__(self, req, hint, category, scope, tlm):
        self.tlm = tlm
        self.requirement = req
        self.hint = hint
        self.category = category
        self.scope = scope #document object that this question belongs to 
        return

    @staticmethod
    def CreateQuestions(raw_q, scope, tlm):
        logging.info("Creating questions for scope: %s", scope.getName())
        assert("items" in raw_q)
        req = raw_q["requirement"] if "requirement" in raw_q else ""
        hint = raw_q["hint"] if "hint" in raw_q else ""
        category = raw_q["category"] if "category" in raw_q else ""

        qs = []
        for item in raw_q["items"]:
            #default is cloze
            q = QCloze(req, hint, category, item, scope, tlm)
            qs.append(q)
        return qs

    @staticmethod
    def findNodeInScope(scope, node, depth=0):
        if isinstance(scope, dict) or isinstance(scope, OrderedDict):
            for k,v in scope.items():
                if k == node: 
                    return v
                n = TLM_Question.findNodeInScope(v, node, depth+2)
                if n:
                    return n

        if isinstance(scope, list): 
            for s in scope:
                n = TLM_Question.findNodeInScope(s, node, depth+2)
                if n:
                    return n


class QCloze(TLM_Question):
    def __init__(self, req, hint, category, cloze, scope, tlm):
        TLM_Question.__init__(self, req, hint, category, scope, tlm)
        self.raw_content = cloze
        self.processed_raw_content = None
        self.unfilled_cloze = cloze
        self.filled_cloze = cloze
        self.scope = scope

        self.parse_content()
        
    @staticmethod
    def sub_aux(x):
        s = x.group(0).strip()
        if s.find(":")>0:
            sz = int(s.split(":")[0].strip("{"))
        else:
            sz = len(s)-2
        if sz>4:
            e = '__'*sz
        else:
            e = '▢'*sz
        r = re.sub(r'{.*}', "{%s}"%e, s, flags=re.UNICODE)
        return r

    def parse_content(self):
        replace_list = {}
        for s in re.finditer("{{.*?}}", self.raw_content, flags=re.UNICODE):
            kw = s.group(0)[2:-2]
            node = TLM_Question.findNodeInScope(self.scope.raw_data, kw)
            if node:
                replace_list["{{%s}}"%kw] = node

        cloze = self.raw_content 
        for k,w in replace_list.items():
            cloze = re.sub(k, w, cloze, flags=re.UNICODE)
        self.processed_raw_content = cloze
        cloze = re.sub(r"\t", "  ", cloze, re.UNICODE)
        self.filled_cloze = re.sub(r"\n", "<br>", cloze, re.UNICODE)

        #cloze = re.sub(r'{.*?}', r'{____}', cloze, flags=re.UNICODE) 
        #cloze = re.sub(r'{.*?}', lambda x:x.group(0).replace(r'.*', "%s"%("▢"*(len(x.group(0))))), cloze, flags=re.UNICODE)
        cloze = re.sub(r'{.*?}', QCloze.sub_aux, cloze, flags=re.UNICODE)
        cloze = re.sub(r"\n", "<br>", cloze, re.UNICODE)
        self.unfilled_cloze = re.sub(r"\t", "  ", cloze, re.UNICODE)

        self.filled_cloze = re.sub(r"{[0-9]:", "{", self.filled_cloze, re.UNICODE)

        return

    def __repr__(self):
        s = "\n"
        if self.requirement:
            s = s + "Requirement: %s\n"%self.requirement
        if self.hint:
            s = s + "Hint: %s\n"%self.hint
        s = s + "Cloze:\n%s"%self.filled_cloze
        return s

    def genAnki(self):
        """ gen anki import for question """
        """ Fields: unfilled_cloze, filled_cloze, tag, requirement, hint """
        hint = self.hint if self.hint else ""
        requirement = self.requirement if self.requirement else ""
        anki_row = "\t".join([self.filled_cloze, self.unfilled_cloze, hint, "", requirement, self.tlm.tag])
        return anki_row

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
                              cloze_fullHint, "", self.tlm.tag])
        return anki_row

class TLM_test:
    def __init__(self, raw_data, tlm):
        self.tlm = tlm
        self.raw_data = raw_data
        self.questions = []
        self.genQuestions()

    def getName(self):
        return "test"

    def genQuestions(self):
        for q in self.raw_data:
            for obj in TLM_Question.CreateQuestions(q, self, self.tlm):
                self.questions.append(obj)

class TLM_Grammar:
    def __init__(self, grammar, raw_grammar, tlm):
        self.tlm = tlm
        self.grammar = grammar.strip()
        self.raw_data = raw_grammar
        self.clozes = []
        self.questions = []

        self.genQuestions()
        return

    def genFullHintAnkiField(self):
        ret = "<b>语法: %s</b><br>"%self.grammar
        if "clozes" in self.raw_data:
            clozes = "<br>".join(self.raw_data["clozes"])
            clozes = re.sub(r"\n", r"<br>", clozes, flags=re.UNICODE)
            ret = ret + clozes
        return ret

    def getName(self):
        return self.grammar

    def getHint(self):
        return "语法: %s"%self.grammar

    def genQuestions(self):
        if "clozes" in self.raw_data:
            for clz in self.raw_data["clozes"]:
                cloze = TLM_Question_Cloze(clz, self, self.tlm)
                self.clozes.append(cloze)
                cloze.genAnki()

        if "questions" in self.raw_data:
            for q in self.raw_data["questions"]:
                for obj in TLM_Question.CreateQuestions(q, self, self.tlm):
                    self.questions.append(obj)

        return


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

        self.questions = []
        self.genQuestions()

        return

    def genQuestions(self):
        if "clozes" in self.raw_data:
            for clz in self.raw_data["clozes"]:
                cloze = TLM_Question_Cloze(clz, self, self.tlm)
                self.clozes.append(cloze)
                cloze.genAnki()

        if "questions" in self.raw_data:
            for q in self.raw_data["questions"]:
                for obj in TLM_Question.CreateQuestions(q, self, self.tlm):
                    self.questions.append(obj)

        return

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

    def getName(self):
        return self.title

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

        for paragraph in self.paragraphs:
            paragraph = paragraph.strip()
            for tok in jieba.cut(paragraph, cut_all=False):
                if re.search(r"[   :!！\b\n\r\t.\"‘“”。，\]\[]", tok, re.UNICODE):
                    continue
                if not tok in self.words:
                    self.words.append(tok)

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
        if not "articles" in self.orig_doc:
            self.text["articles"] = []
        else:
            self.text["articles"] = self.orig_doc["articles"]

        if "grammars" in self.orig_doc:
            self.text["grammars"] = self.orig_doc["grammars"]
        else:
            self.text["grammars"] = []
        
        if not "read_words" in self.orig_doc:
            self.text["read_words"] = []
        else:
            self.text["read_words"] = self.orig_doc["read_words"]

        if not "test" in self.orig_doc:
            self.text["test"] = []
        else:
            self.text["test"] = self.orig_doc["test"]


        self.testModel = None
        self.articleModels = OrderedDict()
        self.grammarModels = OrderedDict()
        self.wordsModel = {}
        self.dictation_sentences = {}
        self.dictation_words = {}

        self.read_words = {}
        self.process_read_words()

        if "dictation_words" in self.orig_doc:
            self.text["dictation_words"] = self.orig_doc["dictation_words"]
        else:
            self.text["dictation_words"] = []

        self.dictation_wordToSentence = {}

        if "dictation_sentences" in self.orig_doc:
            self.text["dictation_sentences"] = self.orig_doc["dictation_sentences"]
            sts  = self.orig_doc["dictation_sentences"]
            assert isinstance(sts, list)
            for s in sts:
                words = self.build_sentence(s)
                for w in words:
                    if w == "":
                        continue
                    self.wordsModel[w] = True
                    self.dictation_wordToSentence[w] = s
                    self.dictation_words[w] = True
                self.dictation_sentences[s] = True
        else:
            self.text["dictation_sentences"] = []

        if "dictation_words" in self.orig_doc:
            lines = []
            if isinstance(self.orig_doc["dictation_words"], list):
                lines = self.orig_doc["dictation_words"]
            else:
                assert isinstance(self.orig_doc["dictation_words"], str)
                lines = [self.orig_doc["dictation_words"]]
            for line in lines:
                line = line.strip()
                words = re.sub(r"\n", " ", line, re.UNICODE)
                words = words.split()
                for w in words:
                    if w == "":
                        continue
                    self.wordsModel[w] = True
                    self.dictation_words[w] = True

        if "test" in self.text:
            self.testModel = TLM_test(self.text["test"], self)

        for article in self.text["articles"]:
            title = article["title"]
            tm = TLM_Article(article, self)
            self.articleModels[title] = tm

        for grammar in self.text["grammars"]:
            gm = TLM_Grammar(grammar["grammar"], grammar, self)
            self.grammarModels[grammar["grammar"]] = gm

    def process_read_words(self):
        if not self.text["read_words"]:
            return
        if isinstance(self.text["read_words"], list):
            lines = self.text["read_words"]
        else:
            lines = [self.text["read_words"]]
        for line in lines:
            line = line.strip()
            words = line.split()
            for w in words:
                self.read_words[w] = True
                self.wordsModel[w] = True

    def build_sentence(self, s):
        words = []
        for tok in jieba.cut(s, cut_all=False):
            if re.search(r"[   :!！\b\n\r\t.\"‘“”。，\]\[]", tok, re.UNICODE):
                continue
            words.append(tok)
        return words

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
