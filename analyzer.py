import pymongo
import mysql.connector
import urllib3
import datetime
import re
import time
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
        time.sleep(1)
        queryurl = analyzer.ipquerytemplate + ip
        response = analyzer.http.request('GET', queryurl)
        resultbody = response.data.decode('utf8', errors = 'ignore')
        analyzer.parser.feed(resultbody)
        postcode = analyzer.parser.datalist[4]
        print(postcode)
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
            col.update_one({'_id': record['_id']},{'$set', {'processed': True}})
        mydb = mysql.connector.connect(host = analyzer.mysqlhost, user = analyzer.mysqlusername, passwd = analyzer.mysqlpw, database = 'chatlog')
        mycursor = mydb.cursor()
        for entry in entrylist:
            ip = entry[1]
            postcode = self.GetPostCode(ip)
            sqlquery = "INSERT INTO loginrecords (username, ipaddress, logintime, logouttime, postcode) VALUES (%s, %s, '%s', '%s', %s)"            
            result = mycursor.execute(sqlquery, (entry[0], entry[1], entry[2], entry[3], postcode))
            mydb.commit()

