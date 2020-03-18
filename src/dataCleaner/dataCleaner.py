import requests
import pymongo
from bson.json_util import dumps

#1545154 unique records

dbService=pymongo.MongoClient("localhost",27017)
db=dbService["wifiSniffer"]

def cleaning():
    db.rawData.rename("cleaning")
    deleteRedundacies()
    #rimuovi pachetti con rssi sotto un certo valore
    #rimuovi pacchetti notturni
    #rimuovi pacchetti con mac random

    #invia al datamanager


def deleteRedundacies():
    

cleaning()


    
