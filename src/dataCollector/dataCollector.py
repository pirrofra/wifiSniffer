import json
import pymongo
from datetime import datetime


def parseJsonl(path):
        with open(path) as file:
            return [json.loads(line) for line in file]
        raise ValueError("error parsing jsonl file")

def changeTimeStamp(list):
    newlist=[]
    for pack in list:
        time = datetime.strptime(pack["timestamp"], '%Y-%m-%dT%H:%M:%S.%f')
        newdate = datetime.strftime(time,'%Y-%m-%d %H:%M:%S')
        time = datetime.strptime(newdate, "%Y-%m-%d %H:%M:%S")
        pack["timestamp"]=int(datetime.timestamp(time))
        newlist.append(pack)
    return newlist

doc=parseJsonl("./snifferdata.jsonl")
doc=changeTimeStamp(doc)
dbService=pymongo.MongoClient("tmp_database",27017)
db=dbService["wifiSniffer"]
db.rawData.insert_many(doc)
print("DONE")
