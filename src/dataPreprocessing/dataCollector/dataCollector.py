import pymongo
import requests
import hashlib
from time import sleep
from time import time
from datetime import datetime
from bson.son import SON
from os import getenv

#ZDM URL
BACKEND="https://api.zdm.zerynth.com/v1/tsmanager/workspace/" 
#header for making rest request to ZDM
header={}
#date format used by request to ZDM
date="%Y-%m-%dT%H:%M:%SZ"

dbService=pymongo.MongoClient("tmp_database",27017)
db=dbService["wifiSniffer"]


#set header for all the requests to ZDM 
#get JWT token from enviroment variable
def setHeader():
    JWT=getenv("JWT")
    header['Authorization']='Bearer ' + JWT

#add the workspaceID to the URL
#get workspacID from enviroment variable
def getURL(URL):
    workspaceID=getenv("WORKSPACEID")
    URL=URL+workspaceID+"/tag/wifiSniffer"
    return URL

#get all data from ZDM between "start" and "end"
#returns all data as a list of packets
def getDataFromZDM(start,end):
    URL=BACKEND+"?start="+start+"&end="+end+"&size=-1" #URL for the request
    response=requests.get(URL,headers=header)
    packetlst=[]
    data=response.json()
    if(data.get("result")!=None):
        for element in data["result"]:
            try:
                for pkt in element["payload"]["data"]:
                    pkt["timestamp"]=int(pkt["timestamp"])
                    encodedMac=str.encode(pkt["mac2"])
                    pkt["mac2"]=hashlib.md5(encodedMac).hexdigest()
                    packetlst.append(pkt)
            except:
                pass
    return packetlst

#save this date in a colletion
def saveScan(date):
    db.scanList.insert_one({"time":date})

#get the last date from the collection
def getLastScan():
    result=db.scanList.aggregate([
        {"$group":{
            "_id":None,
            "max":{"$max":"$time"}}}])
    return list(result)[0]["max"]

#save data in the "rawData" collection
def saveData(data):
    if len(data)!=0:
        db.rawData.insert_many(data)

#makes a request for data to the ZDM every "time" seconds
#if it's the first time get the most recend date in the collection
def poll(time):
    saveScan("1970-01-01T00:00:00Z")
    lastCall=getLastScan()
    while(True):
        now=datetime.utcnow().strftime(date)
        try:
            data=getDataFromZDM(lastCall,now)
            lastCall=now
            saveData(data)
            saveScan(now)
        except:
            pass
        sleep(time)


BACKEND=getURL(BACKEND)
setHeader()

#infinite loop of request to the ZDM
poll(60)