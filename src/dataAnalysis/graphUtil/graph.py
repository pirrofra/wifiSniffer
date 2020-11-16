class trajectory:
    
    def __init__(self,mac):
        self.mac=mac
        self.locationCount={}
        self.locations={}
        self.slot=0
        self.emptySlots=0

    def addToTrajectory(self,data):
        self.slot=self.slot+1
        if data == None:
            self.emptySlots=self.emptySlots+1
        else:
            count={}
            lastSeen={}
            for element in data:
                if(count.get(element["room"])==None):
                    count[element["room"]]=0
                count[element["room"]]=count[element["room"]]+1
                if(lastSeen.get(element["room"])==None):
                    lastSeen[element["room"]]=0
                lastSeen[element["room"]]=max(lastSeen[element["room"]],element["timestamp"])
            
            Max=0
            Location=None
            for room in count.keys():
                if(count[room]>Max or Max==0):
                    Location=room
                    Max=count[room]
                elif (count[room]==Max and lastSeen[Location]<lastSeen[room]):
                    Location=room
                    Max=count[room]
            timestamp=(lastSeen[Location]//300)*300
            self.locations[timestamp]=Location
            if(self.locationCount.get(Location)==None):
                self.locationCount[Location]=0
            self.locationCount[Location]=self.locationCount[Location]+1


def group(data,names):
    result={}
    Min=Max=data[0]["timestamp"]
    for element in data:
        timestamp=(element["timestamp"]//300)*300
        Min=min(Min,timestamp)
        Max=max(Max,timestamp)
        mac=element["mac"]
        element["room"]=names[element["room"]]
        if(result.get(mac)==None):
            result[mac]={}
        if(result[mac].get(timestamp)==None):
            result[mac][timestamp]=[]
        result[mac][timestamp].append(element)
    return result,Min,Max

def createTrajectories(data,names):
    result=[]
    data,Min,Max=group(data,names)
    for mac in data.keys():
        curr=Min
        tr=trajectory(mac)
        while curr <= Max:
            tr.addToTrajectory(data[mac].get(curr))
            curr=curr+300
        result.append(tr)
    return result,Min,Max

def removeTrajectories(trajectoryList,Tmin,Tmax):
    newResult=[]
    for tr in trajectoryList:
        coef=(tr.slot - tr.emptySlots)/tr.slot
        if(coef>=Tmin and coef<=Tmax):
            newResult.append(tr)
    return newResult

def findWorkplaces(trajectoryList):
    result={}
    for tr in trajectoryList:
        mac=tr.mac
        Max=0
        Workplace=None
        for room in tr.locationCount.keys():
            if(tr.locationCount[room]>Max):
                Max=tr.locationCount[room]
                Workplace=room
        result[mac]=Workplace
    return result
        
def updateGraph(graph,a,b):
    if(graph.get(a)==None):
        graph[a]={}
    if(graph[a].get(b)==None):
        graph[a][b]=0
    graph[a][b]=graph[a][b]+1
    return graph

def createRelationshipGraph(trajectoryList,Min,Max):
    graph={}
    workplaces=findWorkplaces(trajectoryList)
    for tr in trajectoryList:
        workplace=workplaces[tr.mac]
        prev=None
        time=Min
        while(time<=Max):
            if(tr.locations.get(time)==None):
                prev=None
            else:
                current=tr.locations[time]
                if(prev!=None and prev!=current and current != workplace):
                    graph=updateGraph(graph,workplace,current)
                prev=current
            time=time+300
    return graph

def createMovementsGraph(trajectoryList,Min,Max):
    graph={}
    for tr in trajectoryList:
        prev=None
        time=Min
        while(time<=Max):
            if(tr.locations.get(time)==None):
                prev=None
            else:
                current=tr.locations[time]
                if(prev!=None and prev!=current):
                    graph=updateGraph(graph,prev,current)
                prev=current
            time=time+300
    return graph  

def createGraph(data,names,Tmin,Tmax,group):
    trajectoryList,Min,Max=createTrajectories(data,names)
    trajectoryList=removeTrajectories(trajectoryList,Tmin,Tmax)
    if(group==False):
        graph=createMovementsGraph(trajectoryList,Min,Max)
    else:
        graph=createRelationshipGraph(trajectoryList,Min,Max)
    return graph


def getTrajectories(data,names,Tmin,Tmax):
    trajectoryList,Min,Max=createTrajectories(data,names)
    trajectoryList=removeTrajectories(trajectoryList,Tmin,Tmax)
    workplaces=findWorkplaces(trajectoryList)
    result={}
    result["trajectory"]={}
    result["workplace"]={}
    for tr in trajectoryList:
        result["workplace"][tr.mac]=workplaces[tr.mac]
        result["trajectory"][tr.mac]=[]
        time=Min
        while(time<=Max):
            if(tr.locations.get(time)==None):
                result["trajectory"][tr.mac].append(("None",time))
            else:
                current=tr.locations[time]
                result["trajectory"][tr.mac].append((current,time))
            time=time+300
    return result
