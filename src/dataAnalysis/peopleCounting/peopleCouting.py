

class statistics:
    macStates={}
    countedPeople=0
    currentTime=0
    timeline={}
    ArrivalTimeout={}

    def __init__(self,at,wt,dt):
        self.at=at
        self.dt=dt
        self.wt=wt    

    def timeout(self,time):
        tobeConfirmed=[]
        if(self.timeline.get(time)!=None):
            for mac in self.timeline[time]:
                if(self.ArrivalTimeout.get(mac)==time):
                    tobeConfirmed.append(mac)
                    del self.ArrivalTimeout[mac]
                else:
                    (state,slot)=self.timeoutOccured(mac)
                    delta=((slot+1)*60)+time
                    if(state==0):
                        del self.macStates[mac]
                    else:
                        self.macStates[mac]=state,delta
                        self.timelineAppend(mac,delta)
        
            self.arrivalConfirmation(time,tobeConfirmed)
            del self.timeline[time]

    def arrivalConfirmation(self,time,tobeConfirmed):
        for mac in tobeConfirmed:
            if(self.macStates.get(mac)!=None):
                delta=(2*60)+time
                x,oldTime=self.macStates[mac]
                self.macStates[mac]=(2,delta)
                self.timelineAppend(mac,delta)
                self.timeline[oldTime].remove(mac)
                self.countedPeople=self.countedPeople+1

    def addToCount(self,time,spottedMac):
        while(self.currentTime<=time):
            self.timeout(self.currentTime)
            self.currentTime=self.currentTime+60

        for mac in spottedMac:
            if(self.macStates.get(mac)==None):
                state,slot=self.firstArrival(mac)
                arrivaldelta=((self.at+1)*60)+time
                self.timelineAppend(mac,arrivaldelta)
                self.ArrivalTimeout[mac]=arrivaldelta
            else:
                oldState,timeout=self.macStates[mac]
                state,slot=self.spottedRequest(mac)
                (self.timeline[timeout]).remove(mac)                    
            delta=((slot+1)*60)+self.currentTime
            self.timelineAppend(mac,delta)
            self.macStates[mac]=state,delta

    def timelineAppend(self,mac,delta):
        if(self.timeline.get(delta)==None):
            self.timeline[delta]=[]
        self.timeline[delta].append(mac)


    def timeoutOccured(self,mac):
        (state,tmp)=self.macStates[mac]
        if(state==1):
            if(self.ArrivalTimeout.get(mac)!=None):
                time=self.ArrivalTimeout[mac]
                del self.ArrivalTimeout[mac]
                self.timeline[time].remove(mac)
            state=0
            slot=0
        elif(state==2):
            state=3
            slot=self.dt
        elif(state==3):
            state=0
            slot=0
            self.countedPeople=self.countedPeople-1
        return state,slot

    def spottedRequest(self,mac):
        (state,tmp)=self.macStates[mac]
        if(state==1):
            state=1
            slot=self.wt
        elif(state==2):
            state=2
            slot=1
        elif(state==3):
            state=2
            slot=1
        return state,slot
    
    def firstArrival(self,mac):
        return 1,self.wt

def count(data,stats):
    result=[]
    data=groupbyMinute(data,stats)
    first=True
    
    for time in sorted(data.keys()):
        if(first):
            first=False
            stats.currentTime=time
        stats.addToCount(time,data[time])
        result.append({
            "timestamp":time,
            "people":stats.countedPeople
        })
    return result


def groupbyMinute(data,stat):
    result={}
    for element in data:
        newTimeStamp=(element["timestamp"]//60)*60
        mac=element["mac"]
        if(result.get(newTimeStamp)==None):
            result[newTimeStamp]=[]
        result[newTimeStamp].append(mac)
    return result