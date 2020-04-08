import pymongo
from bson.json_util import dumps
from bson.son import SON
from time import sleep
from math import sqrt
import requests


#TODO: Pipeline per l'analisi

#1545154 unique records
#906752 after delete Redundancies
#860033 after outliner remove (300s)
#862597 after outliner remove(1h)
#582427 total

deviceManager="http://data_manager:5000/cleanData"
#deviceManager="http://127.0.0.1:5000/cleanData"

dbService=pymongo.MongoClient("tmp_database",27017)
#dbService=pymongo.MongoClient("localhost",27017)

db=dbService["wifiSniffer"]

def cleaning():
    db.rawData.rename("cleaning")
    deleteRedundacies()
    db.cleaned.rename("cleaning")
    removeOutliner()
    db.cleaned.rename("cleaning")
    highestRSSI()
    data=db.cleaned.find({},{"_id":0})
    data=list(data)
    send(data)
    db.cleaned.drop()
    print("finito")

def deleteRedundacies():
    pipeline=[
        {"$group":
            {"_id": {
                "mac2":"$mac2",
                "scanner_id":"$scanner_id",
                "timestamp":"$timestamp"
                },
            "rssi":{"$max":"$rssi"}}#proviamo max al posto di push
        },
        {"$project":{
            "_id":0,
            "mac":"$_id.mac2",
            "scanner_id":"$_id.scanner_id",
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
    removeLowRSSI(-91)
    min,max=getMinMax()
    removeOutlinerInterval(min,max+1)
    db.cleaning.drop()

def removeOutlinerInterval(start,end):
    dic=getAvgStdDev(start,end)
    query={"timestamp":{"$lt":end,"$gte":start}}
    elements=list(db.cleaning.find(query))
    cleaned=[]
    for element in elements:
        (avg,stddev)=dic[element["scanner_id"]]
        if(stddev!=0):
            d=(element["rssi"]-avg)/stddev
            if(d<=2 and d>=-2):
                cleaned.append(element)

    if(len(cleaned)!=0):
        db.cleaned.insert_many(cleaned)

def getAvgStdDev(start,end):
    pipeline=[
        {"$match":{"timestamp":{"$lt":end,"$gte":start}}},
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

def removeLowRSSI(low):
    query={"rssi":{"$lte":low}}
    db.cleaning.delete_many(query)


def highestRSSI():
    min,max=getMinMax()
    time=min
    while(time<=max):
        highestRSSIInterval(time,time+60)
        time+=60
    db.cleaning.drop()

def highestRSSIInterval(start,end):
    pipeline=[
        {"$match":{"timestamp":{"$gte":start,"$lt":end}}},
        {"$sort":SON([("mac",1),("rssi",-1)])},
        {"$group":{
            "_id":"$mac",
            "rssi":{"$max":"$rssi"},
            "room":{"$first":"$scanner_id"}}},
        {"$project":{
            "mac":"$_id",
            "rssi":"$rssi",
            "room":"$room"}},
        {"$out":"tmp"}]
    db.cleaning.aggregate(pipeline,allowDiskUse=True)

    join=[
        {"$match":{"timestamp":{"$gte":start,"$lt":end}}},
        {"$lookup":{
            "from":"tmp",
            "localField":"mac",
            "foreignField":"mac",
            "as": "room"}},
        {"$project":{
            "mac":"$mac",
            "scanner_id":"$scanner_id",
            "room":{"$arrayElemAt":["$room",0]},
            "timestamp":"$timestamp",
            "rssi":"$rssi"}},
        {"$project":{
            "mac":"$mac",
            "scanner_id":"$scanner_id",
            "room":"$room.room",
            "timestamp":"$timestamp",
            "rssi":"$rssi"}},
        {"$merge":"cleaned"}]
    db.cleaning.aggregate(join,allowDiskUse=True)


def send(data):
    x = requests.post(deviceManager,json=data)
    while(x.status_code!= 200):
        print(x.text)
        sleep(2)
        x = requests.post(deviceManager,json=data)


def main():
    while(True):
        while(db.rawData.count()==0):
            sleep(180)
        print("iniziato")
        cleaning()
        sleep(180)

main()