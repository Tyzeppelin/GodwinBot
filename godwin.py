#!/usr/bin/python

import sqlite3

import slack
import slack.auth
import slack.channels
import slack.chat
import slack.users

import slacksocket

KEY_WORDS = open("KEY_WORDS", 'r').read().split(",")[:-1]


class NoUserFound(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self, self.value)


class db:

    DB_NAME = "godwin.db"

    def __init__(self):
        self.conn = sqlite3.connect(self.DB_NAME)
        self.cursor = self.conn.cursor()

    def addPoint(self, user):
        self.cursor.execute("update godwin set points=(select points from godwin where user=?)+1 where user=?", [user, user])
        self.conn.commit()

    def addUser(self, user):
        self.cursor.execute("insert into godwin values(?, 1)", [user])
        self.conn.commit()

    def updateUser(self, user):
        test = self.cursor.execute("select points from godwin where user=?", [user])
        print type(test)
        if test.fetchone() is None:
            print "unknown "+user
            self.addUser(user)
            return 1
        else:
            self.addPoint(user)
            return 2

    def getPoints(self, user):
        res = self.cursor.execute("select points from godwin where user=?", [user])
        a = res.fetchone()
        if a is None:
            raise NoUserFound(user)
        else:
            return a[0]

    def getAllPoints(self):
        res = self.cursor.execute("select * from godwin order by points desc")
        return res.fetchall()


def worker(event, db):

    if event[u'type'] == "message":
        try:
            subtype = event[u'subtype']
        except KeyError:
            messageWorker(event, db)
        else:
            subtypedMessageWorker(event, db)


def messageWorker(message, db):
    if message[u'channel']=="botbotbot":
        if "!leaderboard" in message[u'text']:
            puntos = db.getAllPoints()
            board = leaderboard(puntos)
            slack.chat.post_message(u'#random', board, as_user=u'true')
    if message[u'user'] != 'godwin' and (message[u'channel']=="random" or message[u'channel']=="botbotbot"):
        text = message[u'text'].lower()
        user = message[u'user']
        channel = message[u'channel']
        if worthGodwin(text):
            print "<", channel, ",", user, ">", text
            db.updateUser(user)
            state = db.getAllPoints()
            print state
            repartie = "Bravo @"+user+", tu gagnes un point Godwin! :thumbsup:"
            slack.chat.post_message(u'#'+channel, repartie, as_user=u'true')


def subtypedMessageWorker(subtyped, db):
    None


def worthGodwin(sentence):
    for e in KEY_WORDS:
        #print sentence, e
        if e in sentence:
            return True
    return False


def leaderboard(puntos):
    res = u'*Leaderboard*\n'
    i = 1
    for guy in puntos:
        res += str(i)+u'. '+u'@'+guy[0]+u' : '+str(guy[1])+u'pts\n'
        i+=1
    return res


if __name__ == "__main__":

    print "The almighty Godwin-Bot"

    print "\t==== Init API ===="
    TOKEN = open("API_TOKEN", 'r').read(41)

    slack.api_token = TOKEN
    a = slack.auth.test()
    print(a)
    ws = slacksocket.SlackSocket(TOKEN)
    print ("gut.")

    print "\t==== Init DB  ===="
    godwindb = db()
    print godwindb.getAllPoints()
    print "niceru"

    print "=========================="

    #slack.chat.post_message(u'#random', "Bonjour !", as_user=u'true')

    for event in ws.events():
        try:
            ev = event.event
            print event.event
            worker(ev, godwindb)
        except Exception as detail:
            print "test", detail
