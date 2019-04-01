import pymongo
import mysql.connector
import urllib3
import datetime
import re


class analyzer :
    mysqlhost = '118.27.35.79'
    mysqlusername = 'collindoyle'
    mysqlpw = 'Tatsumi1983'
    pcquerytemplate = ''
    ipquerytemplate = 'http://keiromichi.com/index.php?ip='
    mongourl = 'mongodb://118.27.35.79:27017'
    logdict = dict()
    http = urllib3.PoolManager()
    def GetPostCode(self, ip):
        queryurl = analyzer.ipquerytemplate + ip
        response = http.request('GET',queryurl)
        pass

    def ProcessLogs(self):
        mongoclient = pymongo.MongoClient(mongourl)
        query = {'processed': 'False'}
        db = mongoclient['chatlog']
        col = db['chatlog']
        records = list()
        entrylist = list()
        for x in col.find(query):
            records.append(x)
        for record in records:
            t = (record['name'], record['ip'])
            if record['login']:
                if t in logdict:
                    timeindict = logdict[t]['timestamp']
                    if timeindict < record['timestamp']:
                        logdict[t] = record
                else:
                    logdict[t] = record
            else:
                if t in logdict:
                    r = logdict[t]
                    if record['timestamp'] < r['timestamp']:
                        continue
                    logdict.pop(t)
                    entry = (r['name'],r['ip'],r['timestamp'],record['timestamp'])
                    entrylist.append(entry)
        mydb = mysql.connector.connect(host = analyzer.mysqlhost, user = analyzer.mysqlusername, passwd = analyzer.mysqlpw, database = 'chatlog')
        mycursor = mydb.cursor()
        for entry in entrylist:
            ip = entry[1]
            mycursor.execute('SELECT * from ')

