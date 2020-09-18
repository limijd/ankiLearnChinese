#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=C0103,W0703,R0902,R1711,C0116,C0115,R1702

"""
Build Multiple Dicts

A MuliDict object will build a dictionary based on current two local dictionaries.

It will provide 3 python dictionaries:

allChars{}  =>  class ChChar dictionary
    keys: ["word", "oldword", "strokes", "pinyin", "radicals", "explanation",
           "more", "x7explanation"]

allWords{}  => class ChWord dictionary
    keys = ["ci", "explanation", "x7explanation"]

allIdioms{} => class ChIdiom dictionary
    keys = ["word", "pinyin", "abbrivation", "derivation", "example",
            "explanation", "x7explanation"]

"x7explanation" is well formatted. "explanation" field is messy and will be discarded soon.

"""
import os
import json
import logging
import gzip

SCRIPT_PATH=os.path.dirname(os.path.realpath(__file__))

WORD_JSON="%s/dicts/word"%SCRIPT_PATH
CI_JSON="%s/dicts/ci"%SCRIPT_PATH
IDIOM_JSON="%s/dicts/idiom"%SCRIPT_PATH
XIEHOUYU_JSON="%s/dicts/xiehouyu"%SCRIPT_PATH
WEBDICT_FREQ="%s/dicts/freq/stdzn.webdict.freq"%SCRIPT_PATH
X7_DICT="%s/dicts/x7"%SCRIPT_PATH

class MultiChineseDict:
    def __init__(self):
        self.jsWord = MultiChineseDict.loadJS(WORD_JSON)
        self.jsCi = MultiChineseDict.loadJS(CI_JSON)
        self.jsIdiom = MultiChineseDict.loadJS(IDIOM_JSON)
        self.jsXiehouyu = MultiChineseDict.loadJS(XIEHOUYU_JSON)

        self.allChars = {} #所有汉字
        self.allWords = {} #所有词语
        self.allIdioms = {} #所有成语
        self.x7ChWords = {} #x7字典

        self.allFreq = {} #webdict 词频数据

        self.build()

    def lookup(self, s):
        if len(s) == 1:
            return self.allChars[s]

        if s in self.allIdioms:
            return self.allIdioms[s]

        return self.allWords[s]

    @staticmethod
    def loadJS(jsonFile):
        fp = gzip.GzipFile(jsonFile, "r")
        return json.load(fp)

    def buildChChars(self):
        for word in self.jsWord:
            cc = ChChar(word["word"], word)
            self.allChars[word["word"]] = cc
            if cc.char in self.allFreq:
                cc.freq = self.allFreq[cc.char][1]
            if cc.char in self.x7ChWords:
                cc.raw_js["x7explanation"] = self.x7ChWords[cc.char]
        logging.info("load %d 单字 from webdict", len(self.allChars))
        return

    def buildChIdioms(self):
        for idiom in self.jsIdiom:
            idm = ChIdiom(idiom["word"], idiom)
            self.allIdioms[idiom["word"]] = idm
            if idm.idiom in self.x7ChWords:
                idm.raw_js["x7explanation"] = self.x7ChWords[idm.idiom]
            if idm.idiom in self.allFreq:
                idm.freq = self.allFreq[idm.idiom][1]
            if idm.freq > 0: #去除冷门
                for ch in list(set(list(idm.idiom))):
                    if ch in self.allChars:
                        cc = self.allChars[ch]
                        cc.idioms.append(idm)
        logging.info("load %d 成语 from webdict", len(self.allIdioms))
        return

    def buildChWords(self):
        num_ch_in_words = 0
        for ci in self.jsCi:
            if len(ci["ci"])==1:
                num_ch_in_words = num_ch_in_words + 1
                continue
            cw = ChWord(ci["ci"], ci)
            self.allWords[ci["ci"]] = cw
            if cw.word in self.x7ChWords:
                cw.raw_js["x7explanation"] = self.x7ChWords[cw.word]
            if cw.word in self.allFreq:
                cw.freq = self.allFreq[cw.word][1]
            if cw.freq > 0: #去除冷门
                if not cw.word in self.allIdioms:
                    for ch in list(set(list(cw.word))):
                        if ch in self.allChars:
                            cc = self.allChars[ch]
                            cc.words.append(cw)
        logging.info("Ingored %d 单字 from 词语词典", num_ch_in_words)
        logging.info("load %d 词语 from webdict", len(self.allWords))
        return

    def buildChWordsFromX7Dict(self):
        num_new_ch_from_x7 = 0
        num_new_wd_from_x7 = 0
        for w, info in self.x7ChWords.items():
            if len(w) == 1 and not w in self.allChars:
                js = {
                        "word":w,
                        "oldword":None,
                        "strokes":None,
                        "pinyin":info[0][3],
                        "radicals":None,
                        "explanation":None,
                        "more":None,
                        "x7explanation":self.x7ChWords[w]
                     }
                cc = ChChar(w ,js)
                self.allChars[w] = cc
                num_new_ch_from_x7 =  num_new_ch_from_x7 + 1
                if cc.char in self.allFreq:
                    cc.freq = self.allFreq[cc.char][1]

            if len(w)>1 and not w in self.allWords and not w in self.allIdioms:
                cw = ChWord(w, js={"ci":w, "explanation":None, "x7explanation":info})
                self.allWords[w] = cw
                num_new_wd_from_x7 =  num_new_wd_from_x7 + 1
                if cw.word in self.allFreq:
                    cw.freq = self.allFreq[cw.word][1]
                if cw.freq > 0: #去除冷门
                    if not cw.word in self.allIdioms:
                        for ch in list(set(list(cw.word))):
                            if ch in self.allChars:
                                cc = self.allChars[ch]
                                cc.words.append(cw)
        logging.info("add %d new 单字 from x7 dict", num_new_ch_from_x7)
        logging.info("add %d new 词语 from x7 dict", num_new_wd_from_x7)
        return

    def buildChWordsFromFreqList(self):
        num_from_freq = 0
        for ch_w, freq in self.allFreq.items():
            if len(ch_w)==1:
                continue
            if not ch_w  in self.allWords and not ch_w in self.allIdioms:
                #missing words, add to words list
                cw = ChWord(ch_w, js={"ci":ch_w, "explanation":None})
                num_from_freq = num_from_freq + 1
                cw.freq = freq[1]
                self.allWords[ch_w] = cw
                if cw.word in self.x7ChWords:
                    cw.raw_js["x7explanation"] = self.x7ChWords[cw.word]
                if cw.freq > 0: #去除冷门
                    if not cw.word in self.allIdioms:
                        for ch in list(set(list(cw.word))):
                            if ch in self.allChars:
                                cc = self.allChars[ch]
                                cc.words.append(cw)
        logging.info("load %d 词语 from frequency list", num_from_freq)
        return

    def build(self):
        logging.info("build webdict....")
        self.readWebDictFreq()
        self.buildX7()

        self.buildChChars()
        self.buildChIdioms()
        self.buildChWords()
        self.buildChWordsFromX7Dict()
        self.buildChWordsFromFreqList()

        logging.info("Total %d 单字, %d 单词, %d 成语",
                len(self.allChars), len(self.allWords), len(self.allIdioms))

        #sort associated words/idioms of a char by frequency value
        for cc in self.allChars.values():
            cc.words.sort(key=lambda cw: cw.freq, reverse=False) #small is hot
            cc.idioms.sort(key = lambda idm: idm.freq, reverse=False)
        return

    def buildX7(self):
        logging.info("loading x7 dict....")
        fp = gzip.GzipFile(X7_DICT, "r")
        self.x7ChWords = json.load(fp)
        fp.close()
        logging.info("%d words from x7 dict loaded", len(self.x7ChWords))

    @staticmethod
    def prettyX7Explanation(x7e):
        #print(x7e)
        #s = "%s<br>"%x7e[0][0]
        s = ""
        num = 0
        for x in x7e:
            num = num+1
            dummy, cx, pinyin, expl = x
            assert len(x) == 4
            if len(x7e)>1:
                s = s + "<b>/～:%d/</b><br>"%num
            if pinyin:
                s = s + "[%s] " % pinyin
            for c in cx:
                s =  s + "<%s>"%c
            s = s + "<br>"
            for ex in expl:
                s = s + "%s<br>"%ex
            s = s + "<br>"
        return s

    def readWebDictFreq(self):
        fp = gzip.GzipFile(WEBDICT_FREQ, "r")
        for line in fp.readlines():
            line = line.strip()
            ch_w, freq, freq_pos = line.split()
            freq = int(freq)
            freq_pos = int(freq_pos)
            ch_w = ch_w.decode("utf-8")
            self.allFreq[ch_w] = (freq, freq_pos)
        fp.close()

        return

class ChChar:
    """ 汉字 """
    def __init__(self, char, js):
        self.char = char
        self.raw_js = js
        self.keys = ["word", "oldword", "strokes", "pinyin", "radicals",
                     "explanation", "more", "x7explanation"]
        self.raw_js["x7explanation"] = []
        self.freq = 0
        self.words = []
        self.idioms = []

    def getName(self):
        return self.char

    def __repr__(self):
        return "%s , %s, %d"%(self.char, self.raw_js["pinyin"], self.freq)

    @staticmethod
    def num2star(num):
        if num<1000:
            return "★★★★★"
        if num<2500:
            return "★★★★"
        if num<5000:
            return "★★★"
        if num<10000:
            return "★★"
        if num<25000:
            return "★"
        return ""

    def pp(self):
        print("%s [%s] %s"%(self.char, self.raw_js["pinyin"], ChChar.num2star(self.freq)))
        print("\t词语: ", end="")
        for w in self.words[:10]:
            print("%s%s "%(w.word, ChChar.num2star(w.freq)), end="")
        print("")
        print("\t成语: %s"%(" ".join(map(lambda x: x.idiom, self.idioms[0:10]))))
        if self.raw_js["x7explanation"]:
            print("\t解释x7: ")
            for ex in self.raw_js["x7explanation"][0][3]:
                print("\t\t%s"%ex)
        else:
            print("\t解释: %s"%(self.raw_js["explanation"].replace("\n\n","\n\t")))


class ChWord:
    """ 词语 """
    def __init__(self, word, js):
        self.word = word
        self.raw_js = js
        self.keys = ["ci", "explanation", "x7explanation"]
        if not "x7explanation" in js:
            self.raw_js["x7explanation"] = []
        self.freq = 0
        self.chars = list(set(list(word)))

    def getName(self):
        return self.word

    def __repr__(self):
        return "%s, %d" % (self.word, self.freq)

    def pp(self):
        print("%s %s"%(self.word, ChChar.num2star(self.freq)))
        if self.raw_js["x7explanation"]:
            print("\t解释x7: ")
            for ex in self.raw_js["x7explanation"][0][3]:
                print("\t\t%s"%ex)
        elif self.raw_js["explanation"]:
            print("\t解释: %s"%(self.raw_js["explanation"].replace("\n\n","\n\t")))
        else:
            print("解释: <无>")

class ChIdiom:
    """ 成语 """
    def __init__(self, idiom, js):
        self.idiom = idiom
        self.raw_js = js
        self.keys = ["word", "pinyin", "abbrivation", "derivation",
                     "example", "explanation", "x7explanation"]
        self.raw_js["x7explanation"] = []
        self.freq = 0
        self.chars = list(set(list(idiom)))

    def getName(self):
        return self.idiom

    def __repr__(self):
        return "%s, %d" % (self.idiom, self.freq)

    def pp(self):
        print("%s [%s] %s"%(self.idiom, self.raw_js["pinyin"], ChChar.num2star(self.freq)))
        if self.raw_js["x7explanation"]:
            print("\t解释x7: ")
            for ex in self.raw_js["x7explanation"][0][3]:
                print("\t\t%s"%ex)
        elif self.raw_js["explanation"]:
            print("\t解释: %s"%(self.raw_js["explanation"].replace("\n\n","\n\t")))
        else:
            print("解释: <无>")

if __name__ == "__main__":
    logging.basicConfig(format='[MultiChineseDict: %(asctime)s %(levelname)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

    md = MultiChineseDict()
    md.lookup("天").pp()
