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
    userInfoMap = dict()
    userNameMap = dict()
    IpUserMap = dict()
    idcount = 0
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
        recordcol = db['records']        
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
        for entry in entrylist:
            ip = entry[1]
            postcode = self.GetPostCode(ip)
            print(entry[0] + ': ' + entry[1] + ': ' + postcode)
            dataobj = dict({'username': entry[0], 'ipaddress': entry[1], 'logintime': entry[2], 'logouttime': entry[3], 'postcode': postcode, 'processed': False})
            recordcol.insert_one(dataobj)
        
    def RecognizeUser(self):
        if len(analyzer.userInfoMap) == 0:
            self.LoadUserInfo()
        mongoclient = pymongo.MongoClient(analyzer.mongourl)
        db = mongoclient['chatlog']
        col = db['records']
        lst = list(col.find({'processed': False}))
        createcount = 0       
        for record in lst:
            entryuserid=0            
            isNewUser = False
            if record['username'] not in analyzer.userNameMap.keys() and record['ipaddress'] not in analyzer.IpUserMap.keys(): 
                # new user and new IP detected                
                entryuserid = analyzer.idcount
                analyzer.idcount += 1
                analyzer.userInfoMap[entryuserid] = {'users': {record['username']}, 'ips': {record['ipaddress']}, 'count': 1, 'firstappeared': record['logintime'], 'lastlogout': record['logouttime'], 'created': True, 'updated': False}
                analyzer.userNameMap[record['username']] = {'userId': entryuserid, 'ips': {record['ipaddress']}}
                analyzer.IpUserMap[record['ipaddress']] = {'userId': entryuserid, 'users': {record['username']}}
                isNewUser = True     
                createcount += 1           
            elif record['username'] not in analyzer.userNameMap.keys():
                # new user and used IP
                entryuserid = analyzer.IpUserMap[record['ipaddress']]['userId']
                analyzer.userNameMap[record['username']] = {'userId': entryuserid, 'ips': {record['ipaddress']}}
                analyzer.IpUserMap[record['ipaddress']]['users'].add(record['username'])
                analyzer.userInfoMap[entryuserid]['users'].add(record['username'])
            elif record['ipaddress'] not in analyzer.IpUserMap.keys():
                # used user and new IP
                entryuserid = analyzer.userNameMap[record['username']]['userId']
                analyzer.IpUserMap[record['ipaddress']] = {'userId': entryuserid, 'users': {record['username']}}
                analyzer.userNameMap[record['username']]['ips'].add(record['ipaddress'])
                analyzer.userInfoMap[entryuserid]['ips'].add(record['ipaddress'])
            else:
                # both used user and IP
                entryuserid = analyzer.userNameMap[record['username']]['userId']
            if not isNewUser:
                analyzer.userInfoMap[entryuserid]['count'] += 1
                analyzer.userInfoMap[entryuserid]['updated'] = True
                if record['logintime'] < analyzer.userInfoMap[entryuserid]['firstappeared']:
                    analyzer.userInfoMap[entryuserid]['firstappeared'] = record['logintime']
                if record['logouttime'] > analyzer.userInfoMap[entryuserid]['lastlogout']:
                    analyzer.userInfoMap[entryuserid]['lastlogout'] = record['logouttime']
            col.update_one({'_id': record['_id']}, {'$set': {'processed': True}})
        print('Found %s new users' % (createcount,))
        self.SaveUserInfo()

    def ParseSet(self, settext):
        memlist = settext.strip("{}").split(", ")
        memset = set({})
        for x in memlist:
            s = x.strip("'")
            s = s.replace(u'\u3000',"")
            memset.add(s)
        return memset

    def LoadUserInfo(self):
        mysqldb = mysql.connector.connect(host=analyzer.mysqlhost, user=analyzer.mysqlusername, passwd=analyzer.mysqlpw, database='chatlog')
        mycursor = mysqldb.cursor()
        sqlquery = "SELECT id, usernames, ipaddresses, count, firstappeared, lastlogout FROM userInfo"
        mycursor.execute(sqlquery)
        lst = mycursor.fetchall()
        analyzer.idcount = len(lst)
        for record in lst:
            userset = self.ParseSet(record[1])
            ipset = self.ParseSet(record[2])
            analyzer.userInfoMap[record[0]]={'users': userset, 'ips': ipset, 'count': record[3], 'firstappeared': record[4], 'lastlogout': record[5], 'created': False, 'updated': False}
            for u in userset:
                analyzer.userNameMap[u] = {'userId': record[0], 'ips': ipset}
            for i in ipset:
                analyzer.IpUserMap[i] = {'userId': record[0], 'users': userset}
        mycursor.close()
        mysqldb.close()
    
    def SaveUserInfo(self):
        mysqldb = mysql.connector.connect(host=analyzer.mysqlhost, user=analyzer.mysqlusername, passwd=analyzer.mysqlpw, database='chatlog')
        mycursor = mysqldb.cursor()
        sqlinsert = "INSERT INTO userInfo (id, usernames, ipaddresses, count, firstappeared, lastlogout) VALUES (%s, %s, %s, %s, %s, %s)"
        sqlupdate = "UPDATE userInfo SET usernames=%s, ipaddresses=%s, count=%s, firstappeared=%s, lastlogout=%s WHERE id=%s"
        for i,r in analyzer.userInfoMap.items():
            if r['created']:
                r['created'] = False
                r['updated'] = False
                mycursor.execute(sqlinsert, (i, str(r['users']).encode(encoding='utf-8'), str(r['ips']), r['count'], r['firstappeared'], r['lastlogout']))
                mysqldb.commit()
            elif r['updated']:
                r['updated'] = False
                mycursor.execute(sqlupdate, (str(r['users']).encode(encoding='utf-8'), str(r['ips']), r['count'], r['firstappeared'], r['lastlogout'], i))
                mysqldb.commit()
        mycursor.close()
        mysqldb.close()

