def getWorkplaceDictionary(data,names):
    dic={}
    for obj in data:
        dic[obj["mac"]]=names[obj["room"]]
    return dic
    


def createGraph(data,workplaces):
    graph={}
    for element in data:
        if(workplaces.get(element["mac"])!=None):
            workplace=workplaces[element["mac"]]
            if(element["roomName"]!=workplace):
                if(graph.get(workplace)==None):
                    graph[workplace]={}
                if(graph[workplace].get(element["roomName"])==None):
                    graph[workplace][element["roomName"]]=0
                graph[workplace][element["roomName"]]=graph[workplace][element["roomName"]]+1
    return graph

def renameData(data,names):
    newData=[]
    for element in data:
        if(names.get(element["room"])):
            element["roomName"]=names[element["room"]]
            newData.append(element)
    return newData


    