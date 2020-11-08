import flask
import pymongo
from bson.json_util import dumps
from bson.son import SON



app=flask.Flask("dataManager")

dbService=pymongo.MongoClient("database",27017)
#dbService=pymongo.MongoClient("localhost",27017)

db=dbService["wifiSniffer"]

#error class, with status code
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

#set error hanlder 
@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

#raise an exception if an error occured, returns data if everything is ok
def createResponse(status,data):
    if(status==0):
        return dumps(data)
    else:
        raise InvalidUsage(data, status_code=400)

#returns all data with timestamp between "start" and "end" by scanners listed in "scanner"
#from cleanData collection
def getCleanData(scanner,start,end):
    if(scanner==None or start==None or end==None):
        result=createResponse(-1,"MissingParameterForSearch")
    else:
        #aggregate insted of find to allow Disk Use
        data=db.cleanData.aggregate([
            {"$match":{
                "room": { "$in": scanner },
                "timestamp":{
                    "$gte":start,
                    "$lt":end}}},
            {"$sort":SON([("timestamp",1),("room",-1)])}
        ],allowDiskUse=True)
        result=createResponse(0,data)
    return result #result of the aggregation in json

#insert "data" in cleanData Collection
def postCleanData(data):
    if(type (data) is not list):
        print(type(data))
        result=createResponse(-1,"Data is not a Json List")
    else:
        db.cleanData.insert_many(data)
        result=createResponse(0,"Success")
    return result

#query that returns a mac address, given a name
def getSingleDevice(name):
    query={"name": name}
    data=db.devices.find(query,{"_id":0})
    return createResponse(0,data)

#add a device name and a mac address in the "devices" collection
def postSingleDevice(name,mac):
    obj={"name":name,"mac":mac}
    db.devices.insert_one(obj)
    return createResponse(0,"Success")

#assign at every mac address spotted a "workplace" (the room where he's most found in)
# def findWorkplace(scanner,start,end):
#     if(scanner==None or start==None or end==None):
#         result=createResponse(-1,"MissingParameterForSearch")
#     else:
#         #group by room and mac
#         #count records
#         #return only the room and where with the highest count
#         pipeline=[
#             {"$match":{"timestamp":{"$gte":start,"$lt":end},"room": { "$in": scanner }}},
#             {"$group":{
#                 "_id":{
#                     "mac":"$mac",
#                     "room":"$room"},
#                 "count":{"$sum":1}}},
#             {"$sort":SON([("_id.mac",1),("count",-1)])},
#             {"$group":{
#                 "_id":"$_id.mac",
#                 "room":{"$first":"$_id.room"},
#                 "count":{"$first":"$count"}}},
#             {"$project":{
#                 "_id":0,
#                 "mac":"$_id",
#                 "room":"$room",
#                 "count":"$count"}}]
#         result= createResponse(0,db.cleanData.aggregate(pipeline,allowDiskUse=True))
#     return result

#route to get or save clean data
#if it's a get request, the json attachment contains
#{start:"start",end:"end",scanner:["scanner1","scanner2", ... "scanner3"]}
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

#get all device saved in "devices" collection
@app.route('/device',methods=['GET'])
def getAllDevices():
    data=db.devices.find({},{"_id":0})
    return createResponse(0,data)

#route to save or get the mac address of a given device name
#if it's a post request, the json attachment is {mac:"mac address"}
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

#route that get all workplaces of devices scanned
# @app.route("/cleanData/workplace",methods=['GET'])
# def workplace():
#     if(flask.request.is_json==False):
#         result=createResponse(-1,"Data is not a Json File")
#     else:
#         data=flask.request.get_json()
#         start=data["start"]
#         end=data["end"]
#         scanner=data["scanner"]
#         result=findWorkplace(scanner,start,end)
#     return result

