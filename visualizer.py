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
    def DrawLoginTimeGraph(self, id):
        if type(id) == int:
            mysqldb = mysql.connector.connect(host=visualizer.mysqlhost, user=visualizer.mysqluser, passwd=visualizer.mysqlpasswd, database='chatlog')
            

