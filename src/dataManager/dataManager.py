import flask
import pymongo
from bson.json_util import dumps
from json import loads


app=flask.Flask("DataManager")
dbService=pymongo.MongoClient("database",27017)
db=dbService["wifiSniffer"]


def createResponse(status,data):
    return {
        "status":status,
        "data":data
    }

def getSniffedData(scanner,start,end):
    result=createResponse(-1,"Generic Error")
    if(scanner==None or start==None or end==None):
        result=createResponse(-1,"MissingParameterForSearch")
    else:
        query={
            "scanner_id": { "$in": scanner },
            "time":{
                "$gte":start,
                "$lt":end
            }
        }
        data=db.sniffedData.find(query,{"_id":0})
        data=dumps(data)
        result=createResponse(0,loads(data))
    return result

def postSniffedData(data):
    result=createResponse(-1,"Generic Error")
    if(type (data) is not list):
        result=createResponse(-1,"Data is not a Json List")
    else:
        db.sniffedData.insert_many(data)
        result=createResponse(0,"Success")
    return result

def getSingleDevice(name):
    query={"name": name}
    data=db.devices.find(query,{"_id":0})
    data=dumps(data)
    return createResponse(0,loads(data))


def postSingleDevice(name,mac):
    obj={"name":name,"mac":mac}
    db.devices.insert_one(obj)
    return createResponse(0,"Success")

@app.route('/sniffedData',methods=['POST', 'GET'])
def sniffedData():
    result=createResponse(-1,"Generic Error")
    if(flask.request.is_json==False):
        result=createResponse(-1,"Data is not a Json File")
    else:
        if flask.request.method== "GET":
            data=flask.request.get_json()
            scanner=data["scanner"]
            start=data["start"]
            end=data["end"]
            result=getSniffedData(scanner,start,end)
        elif flask.request.method=="POST":
            data=flask.request.get_json()
            result=postSniffedData(data)
    return result

@app.route('/device',methods=['GET'])
def getAllDevices():
    data=db.devices.find({},{"_id":0})
    data=dumps(data)
    return createResponse(0,loads(data))

@app.route('/device/<name>',methods=['GET','POST'])
def singleDevice(name):
    result=createResponse(-1,"Generic Error")
    if flask.request.method== "GET":
        result=getSingleDevice(name)
    elif flask.request.method=="POST":
        if(flask.request.is_json==False):
            result=createResponse(-1,"Data is not a Json File")
        else:
            data=flask.request.get_json()
            mac=data["mac"]
            result=postSingleDevice(name,mac)
    return result


#app.run()