# Learning Chinese by using ANKI - 用ANKI学习中文

## Introduction

The tool can process any Chinese text and build an optimal list of Chinese characters/words from the text. The "pinyin" and "definitions" of the characters/words/idioms will also be created for them based on two local good enough dictionaries. Audio of the character/words/text can also be generated. For Chinese characters, a list of high frequency words and idioms will be linked to help learn and understand the character.

All characters/words/idioms have frequency value which was obtained from the webdict database.

Technically I used "Jieba" https://github.com/fxsjy/jieba to tokenize the Chinese text.  Google "text-to-speech" is used to generate waveNet voices which is pretty nice now. Amazon Polly , Xunfei and Microsoft tts can be good alternatives.

Some pre-built resouces are also provided to help you get start. Below notes/cards can be created for various learning requirements.

* 听课文
* 朗读课文
* 学习字词
* 朗读字词
* 默写字词
* 看图认字(TBD)

另外还有支持几种类型的习题

* 完词填空
* 问答题
* 选择题(TBD)
* 拼音题(TBD)
* 测验(TBD)


For un-organized material, only "字词" note type will be created. The note type can support 3 types of card: "学习字词", “朗读字词", “默写字词". 

To build fully functional learning material, the document need to be structurized with a pre-defined YAML format which I call it TLM("Text Lesson Model"). See example.

A simple manual ANKI database python3 "ORM" module is also provided to directly operate the ANKI database. It is useful when you try to analyze the current information in your ANKI decks. For example, I have created a tool to pre-analyze the readings to know how many new words are there. I usually use the script to process readings, books, or even movie captions. If there are too many new words in the material you can choose to import and learn these new words first.

So this is the tips I will strongly recommend . Building a "lifetime Chinese ANKI deck" when you get familiar with ANKI. All of your learned Chinese can be put into the deck tree. Each time when you start new learning material, the existing words will be skipped. You only need to spend a little effort to learn the new words. And then you can focus on the new material itself as quick as possible. Personally I also use this way to learn English. 


## Motivation

I created the tool mainly for helping my kids learn Chinese. And I want to make the effort reusable and inheritable, especially my younger son can also benefit from it.

My pleasure if it happens to help your Chinese learning.

## Status

It's working but not fully productized yet.

## Step by step setup guide

https://github.com/limijd/ankiLearnChinese/wiki/Step-By-Step-Guide

## About

Scan QR code to contact me through email

![alt text](./misc/em.png)

![alt text](./misc/wchat.png)

