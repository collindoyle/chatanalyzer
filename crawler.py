import datetime
import re
import urllib3
import pymongo


class crawler:
    url = "http://partychat1.nazca.co.jp/7/hukesen/chat.cgi?mode=index_flmain"
    mongourl = "mongodb://118.27.35.79:27017"
    lastlogtime = datetime.datetime.fromisoformat("1970-01-01 00:00:00")
    def __init__(self):
        client = pymongo.MongoClient(crawler.mongourl)
        db = client['chatlog']
        collection = db['latestTimeStamp']
        origintimestamp = collection.find_one()['timestamp']
        crawler.lastlogtime = origintimestamp

    def GetPage(self):
        http = urllib3.PoolManager()
        response = http.request('GET', crawler.url)
        logbody = response.data.decode('cp932', errors='ignore')
        loglist = logbody.split('<HR>\n')
        loglist = loglist[1:-1]
        for line in loglist:
            m = re.search('おしらせ', line)
            if m != None:
                mip = re.search('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',line)
                ip = mip.groups()[0]
                m1 = re.search('(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})', line)
                timestring = m1.groups()[0]
                timestamp = datetime.datetime.fromisoformat(timestring)
                dataobj = dict()
                if timestamp > crawler.lastlogtime:
                    lastlogtime = timestamp
                    mName = re.search(':\s(.+)\sさん\u3000',line)
                    name = mName.groups()[0]
                    dataobj['name']=name
                    dataobj['ip']=ip
                    dataobj['timestamp']=timestamp
                    dataobj['processed']=False                    
                    mIn = re.search('ようこそ',line)
                    if mIn != None:
                        login = True
                        dataobj['login']=login
                    else:
                        login = False
                        dataobj['login']=login
                    client = pymongo.MongoClient(crawler.mongourl)
                    db = client['chatlog']
                    collection = db['chatlog']
                    collection.insert_one(dataobj)
                else:
                    pass
            else:
                pass
        timecollection = db['latestTimeStamp']        
        timecollection.find_one_and_update({},{'$set':{'timestamp':crawler.lastlogtime}})
    



