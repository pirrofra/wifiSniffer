import flask
import requests
from datetime import datetime
from json import dumps
import pytz

app=flask.Flask("grafanaRequest")
api="http://data_analysis:5001/api/"


#get timestamp from a date string
def getUnixTime(string):
    date=datetime.strptime(string,"%Y-%m-%dT%H:%M:%S.%fZ")
    date=pytz.utc.localize(date)
    return date.timestamp()

#test route
@app.route("/",methods=['GET'])
def test():
    return "ok"

#search route, returns the metrics used by the query from grafana
@app.route("/search",methods=["GET","POST"])
def search():
    response=requests.get(api+"room")
    data=response.json()
    return dumps(data)

#transform the query request from grafana in request to data_analysis 
@app.route("/query",methods=["GET","POST"])
def query():
    parameters=flask.request.get_json()
    start=getUnixTime(parameters["range"]["from"])
    end=getUnixTime(parameters["range"]["to"])
    #interval=parameters["intervalMs"]//1000
    result=[]
    for target in parameters["targets"]:
        payload={"start":start,"end":end,"at":6,"wt":2,"dt":6} #at, wt, dt default value
        name=target["target"]
        if(target.get("data")!=None):
            additional=target["data"]
            payload["at"]=additional["at"]
            payload["dr"]=additional["dt"]
            payload["wt"]=additional["wt"]
        response=requests.get(api+"peopleCounting/"+name,json=payload)
        datapoints=[]
        data=response.json()
        for point in data:
            a=point["timestamp"]
            b=point["people"]
            if(a>=start):
                datapoints.append([b,a*1000])
        if(target["type"]=="timeserie"):
            result.append({"target":target,"datapoints":datapoints})
        else:
            coloumns=[{"text":"people","type":"number"},{"text":"timestamp","type":"time"}]
            result.append({"coloumns":coloumns,"rows":datapoints,"type":"table"})
    return dumps(result)

#annotations route, no needs to be implemented
@app.route("/annotations",methods=["GET","POST"])
def annotations():
    return {}
        