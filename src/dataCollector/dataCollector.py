import pymongo
import requests
from time import sleep
from time import time
from datetime import datetime
from bson.son import SON


BACKEND="https://api.zdm.zerynth.com/v1/tsmanager/workspace/"
header={}
date="%Y-%m-%dT%H:%M:%SZ"

dbService=pymongo.MongoClient("tmp_database",27017)
db=dbService["wifiSniffer"]


def getLine(path,int):
    file=open(path,"r")
    lines=file.read().split("\n")
    str=lines[int-1]
    file.close()
    return str

def setHeader():
    JWT=getLine("auth",2)
    header['Authorization']='Bearer ' + JWT

def getURL(URL):
    workspaceID=getLine("auth",1)
    URL=URL+workspaceID+"/tag/wifiSniffer"
    return URL

def getDataFromADM(start,end):
    URL=BACKEND+"?start="+start+"&end="+end+"&size=-1"
    print(URL)
    response=requests.get(URL,headers=header)
    packetlst=[]
    data=response.json()
    if(data.get("result")!=None):
        for element in data["result"]:
            try:
                for pkt in element["payload"]["data"]:
                    pkt["timestamp"]=int(pkt["timestamp"])
                    packetlst.append(pkt)
            except:
                pass
    return packetlst

def saveScan(date):
    db.scanList.insert_one({"time":date})

def getLastScan():
    result=db.scanList.aggregate([
        {"$group":{
            "_id":None,
            "max":{"$max":"$time"}}}])
    return list(result)[0]["max"]

def saveData(data):
    if len(data)!=0:
        db.rawData.insert_many(data)

def poll():
    saveScan("1970-01-01T00:00:00Z")
    lastCall=getLastScan()
    while(True):
        now=datetime.utcnow().strftime(date)
        try:
            data=getDataFromADM(lastCall,now)
            lastCall=now
            saveData(data)
            saveScan(now)
        except:
            pass
        sleep(60)

BACKEND=getURL(BACKEND)
setHeader()

poll()