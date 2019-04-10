import matplotlib
import numpy
import pymongo
import mysql.connector


class visualizer:
    mymongourl = 'mongodb://118.27.35.79:27017'
    mysqlhost = '118.27.35.79'
    mysqluser = 'collindoyle'
    mysqlpasswd = 'Tatsumi1983'
    querysql = 'SELECT * FROM userInfo WHERE id=%s'

    def ParseSet(self, settext):
        memlist = settext.strip("{}").split(", ")
        memset = set({})
        for x in memlist:
            s = x.strip("'")
            memset.add(s)
        return memset

    def DrawLoginTimeGraph(self, id):
        if type(id) == int:
            mysqldb = mysql.connector.connect(host=visualizer.mysqlhost, user=visualizer.mysqluser, passwd=visualizer.mysqlpasswd, database='chatlog')
            mycursor = mysqldb.consor()
            mycursor.execute(visualizer.querysql, (id,))
            records = mycursor.fetchall()
            if len(records) > 0:
                record = records[0]
                nameset = self.ParseSet(record[1])
                ipset = self.ParseSet(record[2])



            

