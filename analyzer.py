import pymongo
import mysql.connector
import urllib3
import datetime
import ipqueryhtmlparser
import ipinfo
import codecs
import pprint


class analyzer:
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
        mydb = mysql.connector.connect(host=analyzer.mysqlhost, user=analyzer.mysqlusername, passwd=analyzer.mysqlpw, database='chatlog')
        mycursor = mydb.cursor()
        sqlquery = "INSERT INTO ipInfo (ipaddress, postcode, Country, Prefecture, City, Provider) VALUES (%s, %s, %s, %s, %s, %s)"
        if hasattr(details, 'postal'):
            postal = details.postal
        else:
            postal = '000-0000'
        mycursor.execute(sqlquery, (details.ip, postal, details.country_name, details.region, details.city, details.org))
        mydb.commit()
        mycursor.close()
        mydb.close()
        return postal

    def GetPostCode(self, ip):
        mydb = mysql.connector.connect(host=analyzer.mysqlhost, user=analyzer.mysqlusername, passwd=analyzer.mysqlpw, database='chatlog')
        mycursor = mydb.cursor()
        sqlquery = "SELECT * FROM ipInfo WHERE ipaddress = %s"
        mycursor.execute(sqlquery, (ip,))
        lst = mycursor.fetchall()
        if len(lst) > 0:            
            row = lst[0]
            postcode = row[1]
        else:
            postcode = self.GetIpInfo(ip)
        # mycursor.close()
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
                    entry = (r['name'], r['ip'], r['timestamp'], record['timestamp'])
                    entrylist.append(entry)
                    col.update_one({'_id': r['_id']}, {'$set': {'processed': True}})
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
                analyzer.logdict.pop((remainedrecord['name'], remainedrecord['ip']))
        mydb = mysql.connector.connect(host=analyzer.mysqlhost, user=analyzer.mysqlusername, passwd=analyzer.mysqlpw, database='chatlog')
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

    def RecognizeUser(self):
        mydb = mysql.connector.connect(host=analyzer.mysqlhost, user=analyzer.mysqlusername, passwd=analyzer.mysqlpw, database='chatlog')
        mycursor = mydb.cursor()
        sqlquery = 'SELECT username, ipaddress FROM loginrecords'
        mycursor.execute(sqlquery)
        lst = mycursor.fetchall()
        usertable = dict()
        iptable = dict()
        entrytable = dict()
        idcount = 0
        idcounter = 0
        for x in lst:
            if x not in entrytable:
                entrytable[x] = {'counter': 1}
            else:
                entrytable[x]['counter'] += 1
            if x[0] in usertable:
                if x[1] not in usertable[x[0]]:
                    usertable[x[0]].append(x[1])
            else:
                usertable[x[0]] = [x[1]]
            if x[1] in iptable:
                if x[0] not in iptable[x[1]]:
                    iptable[x[1]].append(x[0])
            else:
                iptable[x[1]] = [x[0]]
        idtable = dict()
        for k in entrytable.keys():
            if 'id' not in entrytable[k]:
                idcount = idcounter
                idcounter += 1
                entrytable[k]['id'] = idcount
                idtable[idcount]={'users':set({k[0]}), 'ips':set({k[1]}), 'counter':0}
                idtable[idcount]['counter'] += entrytable[k]['counter']
                for u in iptable[k[1]]:
                    for i in usertable[k[0]]:
                        if (u,i) in entrytable.keys() and 'id' not in entrytable[(u,i)]:
                            entrytable[(u,i)]['id'] = idcount
                            idtable[idcount]['counter'] += entrytable[(u,i)]['counter']
                            if u not in idtable[idcount]['users']:
                                idtable[idcount]['users'].add(u)
                            if i not in idtable[idcount]['ips']:
                                idtable[idcount]['ips'].add(i)
        entryfile = codecs.open('entrycounts.txt','w', encoding='utf8')
        iptablefile = codecs.open('iptable.txt','w', encoding='utf8')
        usertablefile = codecs.open('usertable.txt','w', encoding='utf8')
        idlistfile = codecs.open('idlist.txt','w',encoding='utf8')
        pprint.pprint(entrytable, entryfile)
        pprint.pprint(usertable, usertablefile)
        pprint.pprint(iptable, iptablefile)
        pprint.pprint(idtable,idlistfile)
        entryfile.close()
        iptablefile.close()
        usertablefile.close()
        mydb.close()

