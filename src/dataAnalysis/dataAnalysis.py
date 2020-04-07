import flask
from flask_cors import CORS
import requests
from peopleCounting import peopleCouting
from flask.json import dumps
from relationshipGraph import relationshipGraph
import Location

dataManager="http://data_manager:5000/"
#dataManager="http://127.0.0.1:5000/cleanData/workplace"

app=flask.Flask("dataAnalysis")
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

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

def getScanners(names):
    result=[]
    for mac in names.keys():
        result.append(mac)
    return result

def getNames(names):
    result={}
    for name in names:
        macs=getSingleName(name)
        for mac in macs:
            result[mac]=name
    return result 

def getSingleName(name):
    result=requests.get(dataManager+"/device/"+name)
    data=result.json()
    macs=[]
    for el in data:
        macs.append(el["mac"])
    return macs

def getWorkplaces(start,end,scanner,names):
    payload={
            "start":start,
            "end":end,
            "scanner":scanner
        }
    result=requests.get(dataManager+"cleanData/workplace",json=payload)
    data=result.json()
    return relationshipGraph.getWorkplaceDictionary(data,names)

def getGraph(start,end,nameList):
    names=getNames(nameList)
    scanners=getScanners(names)
    payload={
        "start":start,
        "end":end,
        "scanner":scanners
    }
    result=requests.get(dataManager+"/cleanData",json=payload)
    data=result.json()
    data=relationshipGraph.renameData(data,names)
    workplaces=getWorkplaces(start,end,scanners,names)
    result=relationshipGraph.createGraph(data,workplaces)
    return result


def getPeopleCount(start,end,scanner,at,wt,dt):
    if(start==None or end==None or scanner==None or at==None or dt==None or wt==None):
        result=createResponse(-1,"MissingParameter")
    elif(at<=0 or dt<=0 or wt<=0):
        result=createResponse(-1,"Invalid Parameters")
    else:
        payload={
            "start":start-1800,
            "end":end+1800,
            "scanner":scanner
        }
        result=requests.get(dataManager+"/cleanData",json=payload)
        data=result.json()
        stats=peopleCouting.statistics(at,wt,dt)
        data=peopleCouting.count(data,stats)
        result=createResponse(0,data)
    return result

@app.route('/api/peopleCounting/<roomName>',methods=['GET'])
def getPeopleinRoom(roomName):
    if(flask.request.is_json==False):
        result=createResponse(-1,"Data is not a Json File")
    else:
        scanners=getSingleName(roomName)
        parameters=flask.request.get_json()
        start=parameters["start"]
        end=parameters["end"]
        at=parameters["at"]
        wt=parameters["wt"]
        dt=parameters["dt"]
        result=getPeopleCount(start,end,scanners,at,wt,dt)
    return result
    
@app.route("/api/relationshipGraph",methods=['GET'])
def getRelationshipGraph():
    if(flask.request.is_json==False):
        result=createResponse(-1,"Data is not a Json File")
    else:
        parameters=flask.request.get_json()
        if(type(parameters["rooms"])!= list):
            result=createResponse(-1,"Rooms is not a List")
        else:
            rooms=parameters["rooms"]
            start=parameters["start"]
            end=parameters["end"]
            if(start==None or end==None or rooms==None):
                result=createResponse(-1,"MissingParameterForSearch")
            else:
                result=createResponse(0,getGraph(start,end,rooms))
    return result            

def roomList():
    response=requests.get(dataManager+"device")
    data=response.json()
    list=[]
    for element in data:
        if(element["name"] not in list):
            list.append(element["name"])
    return list


@app.route("/api/roomList",methods=['GET'])
def getRoomList():
    list=roomList()
    return dumps(list)

@app.route("/api/relationshipGraph/graph.html")
def getGraphHTML():
    start=int(flask.request.args.get("from"))//1000
    end=int(flask.request.args.get("to"))//1000
    list=roomList()
    data=getGraph(start,end,list)
    return flask.render_template("graph.html",arg=data)