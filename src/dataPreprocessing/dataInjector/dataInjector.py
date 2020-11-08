import flask
import pymongo
import hashlib
from bson.json_util import dumps
from bson.son import SON

app=flask.Flask("dataInjector")
dbService=pymongo.MongoClient("tmp_database",27017)
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

def hashMACs(data):
    packetlst=[]
    for pkt in data:
        try:
            encodedMac=str.encode(pkt["mac2"])
            pkt["mac2"]=hashlib.md5(encodedMac).hexdigest()
            packetlst.append(pkt)
        except:
            pass
    return packetlst

#insert "data" in rawData Collection
def postRawData(data):
    if(type (data) is not list):
        print(type(data))
        result=createResponse(-1,"Data is not a Json List")
    else:
        data=hashMACs(data)
        db.cleanData.insert_many(data)
        result=createResponse(0,"Success")
    return result

#set route for rawData
@app.route("/api/rawData",methods=["POST"])
def rawData():
    if(flask.request.is_json==False):
        result=createResponse(-1,"Data is not a Json File")
    else:
        data=flask.request.get_json()
        result=postRawData(data)
    return result