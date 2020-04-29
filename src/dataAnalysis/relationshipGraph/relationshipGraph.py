#creates a workplace dictionary where "mac" is the key of the device spotted
#and the values is the name of the room
def getWorkplaceDictionary(data,names):
    dic={}
    for obj in data:
        dic[obj["mac"]]=names[obj["room"]]
    return dic
    
#create a graph, where the cost on the nodes is the number of people from that workplace that has been spotted in another workplace
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

#add the room name to the data
def renameData(data,names):
    newData=[]
    for element in data:
        if(names.get(element["room"])):
            element["roomName"]=names[element["room"]]
            newData.append(element)
    return newData


    