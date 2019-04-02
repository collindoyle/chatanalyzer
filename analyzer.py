import pymongo
import mysql.connector
import urllib3
import datetime
import re
import ipqueryhtmlparser

class analyzer :
    mysqlhost = '118.27.35.79'
    mysqlusername = 'collindoyle'
    mysqlpw = 'Tatsumi1983'
    pcquerytemplate = ''
    ipquerytemplate = 'http://keiromichi.com/index.php?ip='
    mongourl = 'mongodb://118.27.35.79:27017'
    logdict = dict()
    http = urllib3.PoolManager()
    parser = ipqueryhtmlparser.ipqueryparser()
    def GetPostCode(self, ip):
        queryurl = analyzer.ipquerytemplate + ip
        response = analyzer.http.request('GET', queryurl)
        resultbody = response.data.decode('utf8', errors = 'ignore')
        analyzer.parser.feed(resultbody)
        postcode = analyzer.parser.datalist[4]
        return postcode

    def ProcessLogs(self):
        mongoclient = pymongo.MongoClient(analyzer.mongourl)
        query = {'processed': False}
        db = mongoclient['chatlog']
        col = db['chatlog']
        records = list()
        entrylist = list()
        for x in col.find(query):
            records.append(x)
        for record in records:
            t = (record['name'], record['ip'])
            if record['login']:
                if t in analyzer.logdict:
                    timeindict = analyzer.logdict[t]['timestamp']
                    if timeindict < record['timestamp']:
                        analyzer.logdict[t] = record
                else:
                    analyzer.logdict[t] = record
            else:
                if t in analyzer.logdict:
                    r = analyzer.logdict[t]
                    if record['timestamp'] < r['timestamp']:
                        continue
                    analyzer.logdict.pop(t)
                    entry = (r['name'],r['ip'],r['timestamp'],record['timestamp'])
                    entrylist.append(entry)
        mydb = mysql.connector.connect(host = analyzer.mysqlhost, user = analyzer.mysqlusername, passwd = analyzer.mysqlpw, database = 'chatlog')
        mycursor = mydb.cursor()
        for entry in entrylist:
            ip = entry[1]
            postcode = self.GetPostCode(ip)
            #mycursor.execute('SELECT * from ')
            

