import flask
import pymongo
from bson.json_util import dumps
from bson.son import SON



app=flask.Flask("dataManager")

#dbService=pymongo.MongoClient("database",27017)
dbService=pymongo.MongoClient("localhost",27017)

db=dbService["wifiSniffer"]

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

def createResponse(status,data):
    if(status==0):
        return dumps(data)
    else:
        raise InvalidUsage(data, status_code=400)

def getCleanData(scanner,start,end):
    if(scanner==None or start==None or end==None):
        result=createResponse(-1,"MissingParameterForSearch")
    else:
        query={
            "room": { "$in": scanner },
            "timestamp":{
                "$gte":start,
                "$lt":end
            }
        }
        data=db.cleanData.find(query,{"_id":0})
        result=createResponse(0,data)
    return result

def postCleanData(data):
    if(type (data) is not list):
        print(type(data))
        result=createResponse(-1,"Data is not a Json List")
    else:
        db.cleanData.insert_many(data)
        result=createResponse(0,"Success")
    return result

def getSingleDevice(name):
    query={"name": name}
    data=db.devices.find(query,{"_id":0})
    return createResponse(0,data)


def postSingleDevice(name,mac):
    obj={"name":name,"mac":mac}
    db.devices.insert_one(obj)
    return createResponse(0,"Success")

def findWorkplace(scanner,start,end):
    if(scanner==None or start==None or end==None):
        result=createResponse(-1,"MissingParameterForSearch")
    else:
        pipeline=[
            {"$match":{"timestamp":{"$gte":start,"$lt":end},"room": { "$in": scanner }}},
            {"$group":{
                "_id":{
                    "mac":"$mac",
                    "room":"$room"},
                "count":{"$sum":1}}},
            {"$sort":SON([("_id.mac",1),("count",-1)])},
            {"$group":{
                "_id":"$_id.mac",
                "room":{"$first":"$_id.room"},
                "count":{"$first":"$count"}}},
            {"$project":{
                "_id":0,
                "mac":"$_id",
                "room":"$room",
                "count":"$count"}}]
        result= createResponse(0,db.cleanData.aggregate(pipeline,allowDiskUse=True))
    return result

@app.route('/cleanData',methods=['POST', 'GET'])
def cleanData():
    if(flask.request.is_json==False):
        result=createResponse(-1,"Data is not a Json File")
    else:
        if flask.request.method== "GET":
            data=flask.request.get_json()
            scanner=data["scanner"]
            start=data["start"]
            end=data["end"]
            result=getCleanData(scanner,start,end)
        elif flask.request.method=="POST":
            data=flask.request.get_json()
            result=postCleanData(data)
    return result

@app.route('/device',methods=['GET'])
def getAllDevices():
    data=db.devices.find({},{"_id":0})
    return createResponse(0,data)

@app.route('/device/<name>',methods=['GET','POST'])
def singleDevice(name):
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

@app.route("/cleanData/workplace",methods=['GET'])
def workplace():
    if(flask.request.is_json==False):
        result=createResponse(-1,"Data is not a Json File")
    else:
        data=flask.request.get_json()
        start=data["start"]
        end=data["end"]
        scanner=data["scanner"]
        result=findWorkplace(scanner,start,end)
    return result
