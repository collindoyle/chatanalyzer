import datetime
import re
import urllib3
import pymongo


class crawler:
    url = "http://partychat1.nazca.co.jp/7/hukesen/chat.cgi?mode=index_flmain"
    mongourl = "mongodb://118.27.35.79:27017"
    lastlogtime = datetime.datetime(1970, 1, 1)
    http = urllib3.PoolManager()
    
    def __init__(self):
        client = pymongo.MongoClient(crawler.mongourl)
        self.db = client['chatlog']
        collection = self.db['lastTimeStamp']
        origintimestamp = collection.find_one()['timestamp']
        crawler.lastlogtime = origintimestamp

    def GetPage(self):
        result = 0
        response = crawler.http.request('GET', crawler.url)
        logbody = response.data.decode('cp932', errors='ignore')
        loglist = logbody.split('<HR>\n')
        loglist = loglist[1:-1]
        for line in loglist[::-1]:
            m = re.search('おしらせ', line)
            if m is not None:
                mip = re.search(R'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                ip = mip.groups()[0]
                m1 = re.search(R'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})', line)
                timestring = m1.groups()[0]
                timestamp = datetime.datetime.fromisoformat(timestring)
                dataobj = dict()
                if timestamp > crawler.lastlogtime:
                    crawler.lastlogtime = timestamp
                    mName = re.search(R':\s(.+)\sさん\u3000', line)
                    name = mName.groups()[0]
                    dataobj['name'] = name.replace('\\u3000',"")
                    dataobj['ip'] = ip
                    dataobj['timestamp'] = timestamp
                    dataobj['processed'] = False                    
                    mIn = re.search('ようこそ', line)
                    if mIn is not None:
                        login = True
                        dataobj['login'] = login
                    else:
                        login = False
                        dataobj['login'] = login
                    client = pymongo.MongoClient(crawler.mongourl)
                    self.db = client['chatlog']
                    collection = self.db['chatlog']
                    collection.insert_one(dataobj)
                    result += 1
                else:
                    pass
            else:
                pass
        timecollection = self.db['lastTimeStamp']        
        timecollection.find_one_and_update({}, {'$set': {'timestamp': crawler.lastlogtime}})
        return result
