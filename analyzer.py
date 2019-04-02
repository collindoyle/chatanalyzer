import pymongo
import mysql.connector
import urllib3
import datetime
import re
import time
import ipqueryhtmlparser
import ipinfo

class analyzer :
    mytoken = '7909e13247806a'
    mysqlhost = '118.27.35.79'
    mysqlusername = 'collindoyle'
    mysqlpw = 'Tatsumi1983'
    pcquerytemplate = ''
    ipquerytemplate = 'http://keiromichi.com/index.php?ip='
    mongourl = 'mongodb://118.27.35.79:27017'
    logdict = dict()
    http = urllib3.PoolManager()
    parser = ipqueryhtmlparser.ipqueryparser()
    def GetIpInfo(self, ip):
        handler = ipinfo.getHandler(analyzer.mytoken)
        details = handler.getDetails(ip)
        mydb = mysql.connector.connect(host = analyzer.mysqlhost, user=analyzer.mysqlusername, passwd = analyzer.mysqlpw, database = 'chatlog')
        mycursor = mydb.cursor()
        sqlquery = "INSERT INTO ipInfo (ipaddress, postcode, Country, Prefecture, City, Provider) VALUES (%s, %s, %s, %s, %s, %s)"
        if hasattr(details,'postal'):
            postal = details.postal
        else:
            postal = '000-0000'
        mycursor.execute(sqlquery, (details.ip, postal, details.country_name, details.region, details.city, details.org))
        mydb.commit()
        mycursor.close()
        mydb.close()
        return postal

    def GetPostCode(self, ip):
        mydb = mysql.connector.connect(host = analyzer.mysqlhost, user = analyzer.mysqlusername, passwd = analyzer.mysqlpw, database = 'chatlog')
        mycursor = mydb.cursor()
        sqlquery = "SELECT * FROM ipInfo WHERE ipaddress = %s"
        mycursor.execute(sqlquery, (ip,))
        lst = mycursor.fetchall()
        if len(lst) > 0:            
            row = lst[0]
            postcode = row[1]
        else:
            postcode = self.GetIpInfo(ip)
        #mycursor.close()
        mydb.close()
        return postcode

    def ProcessLogs(self):
        mongoclient = pymongo.MongoClient(analyzer.mongourl)
        query = {'processed': False}
        db = mongoclient['chatlog']
        col = db['chatlog']        
        entrylist = list()
        records = list(col.find(query).sort('timestamp'))
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
                    col.update_one({'_id': r['_id']}, {'$set' : {'processed': True}})
                    col.update_one({'_id': record['_id']}, {'$set': {'processed': True}})
                else:
                    entry = (record['name'], record['ip'], record['timestamp'], record['timestamp'])
                    entrylist.append(entry)
                    col.update_one({'_id': record['_id']}, {'$set': {'processed': True}})
        for remainedrecord in list(analyzer.logdict.values()):
            now = datetime.datetime.now()
            if now - remainedrecord['timestamp'] > datetime.timedelta(days=1):
                entry = (remainedrecord['name'], remainedrecord['ip'], remainedrecord['timestamp'], remainedrecord['timestamp'] + datetime.timedelta(hours = 1))
                entrylist.append(entry)
                col.update_one({'_id': remainedrecord['_id']}, {'$set': {'processed': True}})
                analyzer.logdict.pop((remainedrecord['name'],remainedrecord['ip']))
        mydb = mysql.connector.connect(host = analyzer.mysqlhost, user = analyzer.mysqlusername, passwd = analyzer.mysqlpw, database = 'chatlog')
        mycursor = mydb.cursor()
        for entry in entrylist:
            ip = entry[1]
            postcode = self.GetPostCode(ip)
            print(entry[0] + ': ' + entry[1] + ': ' + postcode)
            sqlquery = "INSERT INTO loginrecords (username, ipaddress, logintime, logouttime, postcode) VALUES (%s, %s, %s, %s, %s)"            
            mycursor.execute(sqlquery, (entry[0], entry[1], entry[2], entry[3], postcode))
            mydb.commit()
        mycursor.close()
        mydb.close()

