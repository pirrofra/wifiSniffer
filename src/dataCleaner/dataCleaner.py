import pymongo
from bson.json_util import dumps
from bson.son import SON
from time import sleep
from math import sqrt
import requests

#1545154 unique records
#906752 after delete Redundancies
#860033 after outliner remove (300s)
#862597 after outliner remove(1h)

deviceManager="http://dataManager:1000/cleanData"
#deviceManager="http://127.0.0.1:5000/cleanData"

#dbService=pymongo.MongoClient("tmpDatabase",27017)
dbService=pymongo.MongoClient("localhost",27017)
db=dbService["wifiSniffer"]

def cleaning():
    db.rawData.rename("cleaning")
    deleteRedundacies()
    db.cleaned.rename("cleaning")
    removeOutliner()
    data=db.cleaned.find({},{"_id":0})
    data=list(data)
    send(data)
    db.cleaned.drop()

def deleteRedundacies():
    pipeline=[
        {"$group":
            {"_id": {
                "mac2":"$mac2",
                "scanner_id":"$scanner_id",
                "timestamp":"$timestamp"
                },
            "rssi":{"$push":"$rssi"}}
        },
        {"$project":{
            "_id":0,
            "mac":"$_id.mac2",
            "scanner_id":"$_id.scanner_id",
            "room":"$_id.scanner_id",
            "timestamp":"$_id.timestamp",
            "rssi":"$rssi"            
        }},
        {"$sort":SON([("timestamp",1),("scanner_id",1)])},
        {"$out":"cleaned"}
    ]
    db.cleaning.aggregate(pipeline,allowDiskUse=True)
    db.cleaning.drop()

def getMinMax():
    pipeline=[
        {"$group":{
            "_id":None,
            "max":{"$max":"$timestamp"},
            "min":{"$min":"$timestamp"}
        }
    }]
    MinMax=list(db.cleaning.aggregate(pipeline,allowDiskUse=True))
    min=MinMax[0]["min"]
    max=MinMax[0]["max"]
    return min,max


def removeOutliner():
    min,max=getMinMax()
    time=min
    while(time<=max):
        removeOutlinerInterval(time,time+120)
        perc= ((time-min)*100)/(max-min)
        print("OUTLINER: "+str(perc)+"%...")
        time+=120

def removeOutlinerInterval(start,end):
    dic=getAvgStdDev(start,end)
    query={"timestamp":{"$lt":end,"$gte":start}}
    elements=list(db.cleaning.find(query))
    cleaned=[]
    for element in elements:
        (avg,stddev)=dic[element["scanner_id"]]
        newRSSI=[]
        for rssi in element["rssi"]:
            if(stddev!=0):
                d=(rssi-avg)/stddev
                if(d<=2 and d>=-2 and rssi>=-90):
                    newRSSI.append(rssi)
        if(len(newRSSI)!=0):
            element["rssi"]=newRSSI
            cleaned.append(element)
    if(len(cleaned)!=0):
        db.cleaned.insert_many(cleaned)

def getAvgStdDev(start,end):
    pipeline=[
        {"$match":{"timestamp":{"$lt":end,"$gte":start}}},
        {"$unwind":"$rssi"},
        {"$sort":SON([("scanner_id",1),("rssi",-1)])},
        {"$group":
            {"_id":"$scanner_id",
            "rssi":{"$push":"$rssi"},
            "stddev":{"$stdDevPop":"$rssi"}}},
        {"$project":{
            "scanner_id":"$_id",
            "rssi":"$rssi",
            "stddev":"$stddev"}}
    ]
    avgs=list(db.cleaning.aggregate(pipeline,allowDiskUse=True))
    dic=dict()
    for el in avgs:
        rssi=el["rssi"]
        n=len(rssi)
        m=0
        if(n%1==0):
            m=rssi[((n+1)//2) - 1]
        else:
            m=(rssi[(n//2)]-rssi[(n//2)-1])/2
        dic[el["scanner_id"]]=(m,el["stddev"])
    return dic


def send(data):
    x = requests.post(deviceManager,json=data)
    while(x.status_code!= 200):
        print(x.text)
        sleep(2)
        x = requests.post(deviceManager,json=data)


def main():
    while(True):
        while(db.rawData.count()==0):
            sleep(120)
        cleaning()
        sleep(120)

main()

    
