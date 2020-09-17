#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=C0103,W0703,R0902,R1711,C0116,C0115

'''
AnkiDataModel.py provides B* classes to represent the tables in ANKI database.
And all class objects will be linked as needed.
'''

import logging
from anki.collection import Collection

class BCollection:
    def __init__(self, col: Collection):
        self.col = col
        self.bdecks = {}
        # cards will not be built by default to avoid memory blowup
        self.bcards = {}
        # notes will not be built by default to avoid memory blowup
        self.bnotes = {}
        self.bnoteTypes = {}
        self.bcardTypes = {}
        self.btags = {}
        self.bfields = {}
        return

    def build(self):
        self.build_decks()
        self.build_noteTypes()
        self.build_cardTypes()
        self.build_tags()
        self.build_fields()
        self.link_all()
        return

    def link_all(self):
        # link BDecks and BNoteTypes
        for bd in self.bdecks.values():
            # all note types
            ntids = bd.queryAllNoteTypes()
            for ntid in ntids:
                bnt = self.bnoteTypes[ntid]
                bd.addBNoteType(bnt)
                bnt.addBDeck(bd)

        # link BDeck, BCardType and BNoteType
        for bct in self.bcardTypes.values():
            bnt = self.bnoteTypes[bct.ntid]
            bnt.addBCardType(bct)
            bct.setBNoteType(bnt)
            for bd in bnt.bdecks.values():
                bd.addBCardType(bct)
                bct.addBDeck(bd)

        # fill BField to BNoteType
        for bf in self.bfields.values():
            bnt = self.bnoteTypes[bf.ntid]
            assert bnt
            bnt.addBField(bf)
            bf.setBNoteType(bnt)

        return

    def build_decks(self):
        logging.debug("building decks...")
        sql_deck = 'select * from decks'
        decks_data = self.col.db.all(sql_deck)
        for d in decks_data:
            bd = BDeck(self, d)
            bd.build()
            self.bdecks[bd.id] = bd
        return

    def build_noteTypes(self):
        logging.debug("building note types...")
        sql = 'select * from notetypes'
        nts = self.col.db.all(sql)
        for nt in nts:
            bnt = BNoteType(self, nt)
            bnt.build()
            self.bnoteTypes[bnt.id] = bnt
        return

    def build_cardTypes(self):
        logging.debug("building card types...")
        sql = "select * from templates"
        tpls = self.col.db.all(sql)
        for t in tpls:
            bc = BCardType(self, t)
            bc.build()
            self.bcardTypes[bc.key] = bc
        return

    def build_tags(self):
        logging.debug("building tags ...")
        sql = "select * from tags"
        tags = self.col.db.all(sql)
        for t in tags:
            bt = BTag(self, t)
            bt.build()
            self.btags[bt.name] = bt
        return

    def build_fields(self):
        logging.debug("building fields...")
        sql = "select * from fields"
        flds = self.col.db.all(sql)
        for fld in flds:
            bf = BField(fld)
            bf.build()
            self.bfields[bf.key] = bf

        return

class BDeck:
    def __init__(self, bcol: BCollection, raw_data):
        self.bcol = bcol
        self.rdata = raw_data
        self.noteTypes = {}
        self.cardTypes = {}
        self.name = None
        self.id = None
        return

    def build(self):
        self.name = self.rdata[1]
        self.id = self.rdata[0]
        return

    def queryAllNoteTypes(self):
        sql_nids = 'select nid from cards where did=%d' % self.id
        sql = 'select DISTINCT mid from notes where id IN ( %s )' % sql_nids
        return map(lambda x:x[0], self.bcol.col.db.all(sql))

    def addBNoteType(self, bnt):
        self.noteTypes[bnt.id] = bnt
        return

    def addBCardType(self, bct):
        self.cardTypes[bct.key] = bct
        return

    def loadBCards(self):
        pass

    def loadBNotes(self):
        pass

    def queryNotes(self):
        sql_nids = 'select nid from cards where did=%d' % self.id
        sql = 'select sfld, flds from notes where id IN ( %s )'%sql_nids
        return self.bcol.col.db.all(sql)

    def __repr__(self):
        return "[%d, %s]" % (self.id, self.name)


class BCard:
    def __init__(self, bcol: BCollection, raw_data):
        self.bcol = bcol
        self.rdata = raw_data
        return

    def build(self):
        print("TBD", self.rdata)
        return

    def __repr__(self):
        return self.rdata

class BNote:
    def __init__(self, bcol: BCollection, raw_data):
        self.bcol = bcol
        self.rdata = raw_data
        return

    def build(self):
        print("TBD", self.rdata)
        return

    def __repr__(self):
        return self.rdata

class BNoteType:
    def __init__(self, bcol: BCollection, raw_data):
        self.bcol = bcol
        self.rdata = raw_data
        self.bdecks = {} #used by these decks
        self.bcardTypes={}
        self.bfields={}
        self.id = None
        self.name = None
        return

    def build(self):
        self.id = self.rdata[0]
        self.name = self.rdata[1]
        return

    def addBDeck(self, bd):
        self.bdecks[bd.id] = bd
        return

    def addBCardType(self, bct):
        self.bcardTypes[bct.key] = bct
        return

    def addBField(self, bf):
        self.bfields[bf.key] = bf
        return

    def __repr__(self):
        return "[%d, %s]"%(self.id, self.name)



class BCardType:
    def __init__(self, bcol: BCollection, raw_data):
        self.bcol = bcol
        self.rdata = raw_data
        self.bdecks = {} #decks that are using this card type
        self.bnt = None
        self.ntid = None
        self.ord = None
        self.name = None
        self.key = None
        return

    def build(self):
        self.ntid, self.ord, self.name = self.rdata[0:3]
        self.key = "%d:%d"%(self.ntid, self.ord)
        return

    def addBDeck(self, bd):
        self.bdecks[bd.id] = bd
        return

    def setBNoteType(self, bnt):
        self.bnt = bnt

    def __repr__(self):
        return '[%s, %d, %d, %s]' % (self.key, self.ntid, self.ord, self.name)

class BTag:
    def __init__(self, bcol: BCollection, raw_data):
        self.bcol = bcol
        self.rdata = raw_data
        self.name = None
        return

    def build(self):
        self.name = self.rdata[0]
        return

    def __repr__(self):
        return self.name

class BField:
    def __init__(self, raw_data):
        self.rdata = raw_data
        self.bnt = None
        self.ntid = None
        self.ord = None
        self.name = None
        self.key = None
        return

    def build(self):
        self.ntid, self.ord, self.name = self.rdata[0:3]
        self.key="%d:%d"%(self.ntid,self.ord)
        return

    def setBNoteType(self,bnt):
        self.bnt = bnt
        return

    def __repr__(self):
        return "%d:%d:%s"%(self.ntid,self.ord, self.name)
