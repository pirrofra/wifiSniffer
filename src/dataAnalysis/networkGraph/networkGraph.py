import requests

#deviceManager="http://data_manager:1000/cleanData/workplace"
deviceManager="http://127.0.0.1:5000/cleanData/workplace"


#TODO: possibilmente muovere la request nell'API
def findWorkplace(start,end,scanner):
    payload={
        "start":start,
        "end":end,
        "scanner":scanner
    }
    result=requests.get(deviceManager,json=payload)
    data=result.json()
    dic={}
    for obj in data:
        dic[obj["mac"]]=obj["room"]
    return dic
    


def createGraph(data,workplaces):
    graph={}
    for element in data:
        if(workplaces.get(element["mac"])!=None):
            workplace=workplaces[element["mac"]]
            if(graph.get(workplace)!=None):
                graph[workplace]={}
            if(graph[workplace].get(element["room"])!=None):
                graph[workplace][element["room"]]=0
            graph[workplace][element["room"]]=graph[workplace][element["room"]]+1
    return graph

findWorkplace(1570605959,1584918747,["30:AE:A4:08:9E:94","24:0A:C4:12:12:5C",
        "30:AE:A4:08:95:C4",
        "3C:71:BF:A6:E0:64",
        "3C:71:BF:A6:E8:20",
        "30:AE:A4:03:C8:A0",
        "CC:50:E3:92:9A:B8",
        "3C:71:BF:A6:E5:84",
        "CC:50:E3:92:9E:58",
        "3C:71:BF:A6:E0:34",
        "3C:71:BF:A6:DE:98",
        "3C:71:BF:CF:09:A4",
        "3C:71:BF:A6:E0:6C"])