import flask
from flask_cors import CORS
import requests
from peopleCounting import peopleCounting
from flask.json import dumps
from graphUtil import graph

dataManager="http://data_manager:5000/"
#dataManager="http://127.0.0.1:5000/cleanData/workplace"

app=flask.Flask("dataAnalysis")
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

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

#get list of macs
def getScanners(names):
    result=[]
    for mac in names.keys():
        result.append(mac)
    return result

#get map of macs and names (for scanners)
def getNames(names):
    result={}
    for name in names:
        macs=getSingleName(name)
        for mac in macs:
            result[mac]=name
    return result 

#get all macs for a single "name"
def getSingleName(name):
    result=requests.get(dataManager+"/device/"+name)
    data=result.json()
    macs=[]
    for el in data:
        macs.append(el["mac"])
    return macs


#get data from dataManager, gives them to the graphing algorithm
def getGraph(start,end,nameList,Tmin,Tmax,group):
    names=getNames(nameList)
    scanners=getScanners(names)
    payload={
        "start":start,
        "end":end,
        "scanner":scanners
    }
    result=requests.get(dataManager+"/cleanData",json=payload)
    data=result.json()
    result=graph.createGraph(data,names,Tmin,Tmax,group)
    return result


def filterData(data,start,end):
    newlist=[]
    for pack in data:
        if(pack["timestamp"]>=start and pack["timestamp"]<=end):
            newlist.append(pack)
    return newlist

#get data from dataManager, gives them to the people counting algorithm
def getPeopleCount(start,end,scanner,at,wt,dt):
    if(start==None or end==None or scanner==None or at==None or dt==None or wt==None):
        result=createResponse(-1,"MissingParameter")
    elif(at<=0 or dt<=0 or wt<=0):
        result=createResponse(-1,"Invalid Parameters")
    else:
        #30 min before, 30 min after
        payload={
            "start":start-1800,
            "end":end+1800,
            "scanner":scanner
        }
        result=requests.get(dataManager+"/cleanData",json=payload)
        data=result.json()
        stats=peopleCounting.statistics(at,wt,dt)
        data=peopleCounting.count(data,stats)
        data=filterData(data,start,end)
        result=createResponse(0,data)
    return result

#route that returns the result of the people counting algorithm for every seconds
@app.route('/api/peopleCounting/<roomName>',methods=['GET'])
def getPeopleinRoom(roomName):
    if(flask.request.is_json==False):
        result=createResponse(-1,"Data is not a Json File")
    else:
        scanners=getSingleName(roomName)
        parameters=flask.request.get_json()
        start=parameters["start"]
        end=parameters["end"]
        try:
            at=parameters["at"]
            wt=parameters["wt"]
            dt=parameters["dt"]
        except:
            at=6
            wt=2
            dt=6
            
        result=getPeopleCount(start,end,scanners,at,wt,dt)
    return result
    
#route that returns the relationship graph in json
@app.route("/api/relationshipGraph",methods=['GET'])
def getRelationshipGraph():
    if(flask.request.is_json==False):
        result=createResponse(-1,"Data is not a Json File")
    else:
        parameters=flask.request.get_json()
        if(type(parameters["rooms"])!= list):
            result=createResponse(-1,"Rooms is not a List")
        else:
            #get parameters from json attachment
            rooms=parameters["rooms"]
            start=parameters["start"]
            end=parameters["end"]
            try:
                Tmin=parameters["Tmin"]
                Tmax=parameters["Tmax"]
            except:
                Tmin=0.01
                Tmax=0.5
            if(start==None or end==None or rooms==None):
                result=createResponse(-1,"MissingParameterForSearch")
            else:
                result=createResponse(0,getGraph(start,end,rooms,Tmin,Tmax,True))
    return result            

#route that returns the movements graph in json
@app.route("/api/movementGraph",methods=['GET'])
def getMovementGraph():
    if(flask.request.is_json==False):
        result=createResponse(-1,"Data is not a Json File")
    else:
        parameters=flask.request.get_json()
        if(type(parameters["rooms"])!= list):
            result=createResponse(-1,"Rooms is not a List")
        else:
            #get parameters from json attachment
            rooms=parameters["rooms"]
            start=parameters["start"]
            end=parameters["end"]
            try:
                Tmin=parameters["Tmin"]
                Tmax=parameters["Tmax"]
            except:
                Tmin=0.01
                Tmax=0.5
            if(start==None or end==None or rooms==None):
                result=createResponse(-1,"MissingParameterForSearch")
            else:
                result=createResponse(0,getGraph(start,end,rooms,Tmin,Tmax,False))
    return result 


#request to the dataManager that returns the list of devices
def roomList():
    response=requests.get(dataManager+"device")
    data=response.json()
    list=[]
    for element in data:
        if(element["name"] not in list):
            list.append(element["name"])
    return list

#get all scanners devices
@app.route("/api/room",methods=['GET'])
def getRoomList():
    list=roomList()
    return dumps(list)

#route to get an html page with the relationship graph
@app.route("/api/relationshipGraph/graph.html")
def getGraphHTML():
    start=int(flask.request.args.get("from"))//1000
    end=int(flask.request.args.get("to"))//1000
    list=roomList()
    data=getGraph(start,end,list,0.01,0.5,True)
    return flask.render_template("graph.html",arg=data)

#route to get and register new devices scanner
@app.route("/api/room/<name>",methods=['GET','POST'])
def room(name):
    if flask.request.method== "GET":
        #get, return data
        result=requests.get(dataManager+"device/"+name)
        return result.json()
    else:
        #post, save data
        payload=flask.request.get_json()
        result=requests.post(dataManager+"device/"+name,json=payload)
        return result.json()