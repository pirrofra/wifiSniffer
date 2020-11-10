import pymongo
import time
from bson.json_util import dumps
from bson.son import SON
from time import sleep
from math import sqrt
import requests
import hashlib



dataManager="http://data_manager:5000/cleanData"
#dataManager="http://127.0.0.1:5000/cleanData"

dbService=pymongo.MongoClient("tmp_database",27017)
#dbService=pymongo.MongoClient("localhost",27017)

db=dbService["wifiSniffer"]


def cleaning():
    try:
        start=time.time()
        db.rawData.rename("cleaning")
        hashmacs()
        db.cleaned.rename("cleaning")
        deleteRedundacies()
        db.cleaned.rename("cleaning")
        removeOutliner()
        db.cleaned.rename("cleaning")
        highestRSSI()
        end=time.time()
        elapsed=end-start
        print("TIME USED FOR CLEANING: "+str(elapsed)+" seconds",flush=True)
        data=db.cleaned.find({},{"_id":0})
        data=list(data)
        send(data)
        db.cleaned.drop()
    except:
        pass


def hashmacs():
    packetlst=[]
    data=db.cleaning.find({},{"_id":0})
    data=list(data)
    for pkt in data:
        encodedMac=str.encode(pkt["mac2"])
        pkt["mac2"]=hashlib.md5(encodedMac).hexdigest()
        packetlst.append(pkt)
    db.cleaning.drop()
    db.cleaned.insert_many(data)


#delete packets redundancies
#if the same mac address has been spotted by the same scanner in the same seconds, only saves the one with the highest RSSI
def deleteRedundacies():

    #group by mac, scanner_id and timestamp
    #get the highest rssi
    #rename mac2 field as just mac
    #sort by timestamp
    #"cleaned" collection used as a temporary collection
    pipeline=[
        {"$group":
            {"_id": {
                "mac2":"$mac2",
                "scanner_id":"$scanner_id",
                "timestamp":"$timestamp"
                },
            "rssi":{"$max":"$rssi"}}
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
    db.cleaning.drop() #cleaning collection dropped after all redundancies are deleted

#get highest and lowest timestamp
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

#remove the outliner from all packets sniffed
def removeOutliner():
    #removeLowRSSI(-91)
    min,max=getMinMax()
    while(min<=max):
        removeOutlinerInterval(min,min+300)
        min=min+300
    db.cleaning.drop()

#remove the outliner in the "start" and "end" interval
def removeOutlinerInterval(start,end):
    #get the median and standard deviation for every packet spotted by a scanner
    dic=getAvgStdDev(start,end)
    query={"timestamp":{"$lt":end,"$gte":start}}
    #get all data and stores in a list
    elements=list(db.cleaning.find(query))
    cleaned=[]
    #if a packet has an RSSI below/higher then a certain value is deleted
    for element in elements:
        (avg,stddev)=dic[element["scanner_id"]]
        if(stddev!=0):
            d=(element["rssi"]-avg)/stddev
            if(d<=2 and d>=-2):
                cleaned.append(element)

    if(len(cleaned)!=0):
        db.cleaned.insert_many(cleaned)

#get the standard deviation and the median of RSSI sniffed by a scanner in an interval
#std. dev is automatically calculated by the aggregation
#median is calculated manually, with a list of rssi spotted
def getAvgStdDev(start,end): 
    #aggregation that returns the std dev and the list of rssi spotted
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
    #get the median analyzing the list of rssi spotted
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

#remove all packets with an rssi below a certain value
#NOT USED
def removeLowRSSI(low):
    query={"rssi":{"$lte":low}}
    db.cleaning.delete_many(query)

#assign to every packet the scanner that registered the highest rssi in an interval of 60 seconds
def highestRSSI():
    min,max=getMinMax()
    time=min
    #iterates with data in 60 seconds slot
    while(time<=max):
        highestRSSIInterval(time,time+60)
        time+=60
    db.cleaning.drop()

#assign to every packet the scanner that registered the highest rssi in the "start" "end" interval
def highestRSSIInterval(start,end):

    #get data in the correct interval
    #sort by mac and rssi
    #group by mac, and stores in room the scanner_id with the highest rssi value
    #save data in a tmp collection
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

    #join between data in the interval and the tmp collection
    #every packet now has a field "room" where is specified who spotted the highest rssi value
    #only packets with scanner_id = room are saved.
    #mac in cleaning and mac in tmp as used as field in the join
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
            {"$match":{"$expr":{"$eq":["$room","$scanner_id"]} }},
        {"$merge":"cleaned"}]
    db.cleaning.aggregate(join,allowDiskUse=True)

#send data to the data manager container
def send(data):
    x = requests.post(dataManager,json=data)
    while(x.status_code!= 200):
        print(x.text)
        sleep(2)
        x = requests.post(dataManager,json=data)

#every "time" seconds checks if data has been stored in "rawData" then starts cleaning
def main(time):
    while(True):
        while(db.rawData.count_documents({})==0):
            sleep(time)
        cleaning()
        sleep(time)

#sleeps every 120 seconds
main(300)