import pymongo
from bson.json_util import dumps
from bson.son import SON

#1545154 unique records
#906752 after delete Redundancies

dbService=pymongo.MongoClient("localhost",27017)
db=dbService["wifiSniffer"]

def cleaning():
    #db.rawData.rename("cleaning")
    deleteRedundacies()

    #rimuovi pachetti con rssi sotto un certo valore
    #rimuovi pacchetti notturni
    #rimuovi pacchetti con mac random
    #trasforma in un file json
    #invia al datamanager


def deleteRedundacies():
    pipeline=[
        {"$group":
            {"_id": {
                "mac1":"$mac1",
                "mac2":"$mac2",
                "mac3":"$mac3",
                "mac4":"$mac4",
                "scanner_id":"$scanner_id",
                "timestamp":"$timestamp"
                },
            "rssi":{"$avg":"$rssi"}}
        },
        {"$project":{
            "_id":0,
            "mac1":"$_id.mac1",
            "mac2":"$_id.mac2",
            "mac3":"$_id.mac3",
            "mac4":"$_id.mac4",
            "scanner_id":"$_id.scanner_id",
            "timestamp":"$_id.timestamp",
            "rssi":"$rssi"
        }},
        {"$sort":SON([("timestamp",1),("scanner_id",1)])},
        {"$out":"cleaned"}
    ]
    db.cleaning.aggregate(pipeline,allowDiskUse=True)

cleaning()


    
