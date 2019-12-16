import pandas as pd
import json
from datetime import datetime, timedelta



class dataAnalyzer:
    
    dataFrame = None
    rooms=None
    macPrefixes=None
    contiguousRooms=None
    resampleRule="15Min"
    nightTimeStart=20
    nightTimeEnd=8

    def __init__ (self):
        self.dataFrame = pd.DataFrame()
        

    @staticmethod
    def __convertTimeStamp(dataframe):
        df_ts = dataframe['timestamp'][:].tolist()
        dates =[]
        
        for i in range(0,len(df_ts)):
            
            ts = df_ts[i]
            time = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.%f')
            mydate = datetime.strftime(time,'%Y-%m-%d %H:%M:%S')
            mydate_date = datetime.strptime(mydate, "%Y-%m-%d %H:%M:%S")
            dates.append(mydate_date)
            
        dataframe['date'] = dates
        dataframe.drop('timestamp', axis=1, inplace=True)
        return dataframe

    @staticmethod
    def __parseJsonl(path):
        with open(path) as file:
            return [json.loads(line) for line in file]
        raise ValueError("error parsing jsonl file")

    @staticmethod
    def __parseJson(path):
        with open(path) as file:
            jsonParsed = json.load(file)
        return jsonParsed

    @staticmethod
    def __isADuplicate(pkt1,pkt2):
        time1, time2 = datetime.fromisoformat(pkt1['timestamp']), datetime.fromisoformat(pkt2['timestamp'])
        return (pkt1['mac2'] == pkt2['mac2'] and pkt1['room'] == pkt2['room'] and abs(time1 - time2) < timedelta(seconds=1))

    def __isValidMac(self, mac):
        prefix=mac[:8]
        return prefix in self.macPrefixes

    def __isNight(self,date):
        return date.hour >= self.nightTimeStart or date.hour < self.nightTimeEnd

    def __child(self,newDf):
        newDataAnalyzer=dataAnalyzer()
        newDataAnalyzer.rooms=self.rooms
        newDataAnalyzer.resampleRule=self.resampleRule
        newDataAnalyzer.dataFrame=newDf
        newDataAnalyzer.nightTimeEnd=self.nightTimeEnd
        newDataAnalyzer.nightTimeStart=self.nightTimeStart
        return newDataAnalyzer

    def __filterMac(self,data):
        filteredData=[]
        for packet in data:
            if(self.__isValidMac(packet['mac2'])):
                sniffer_id = packet['scanner_id']
                if sniffer_id in self.rooms:
                    packet['room'] = self.rooms[sniffer_id]
                    filteredData.append(packet)
        return filteredData

    
    def __removeDuplicate(self,data):
        filteredData=[]
        last=None
        for packet in data:
            if last and not self.__isADuplicate(last,packet):
                filteredData.append(packet)
            last=packet
        return filteredData

    def __removeNightTime(self,data):
        nightMacs={}
        for packet in data:
            if self.__isNight(datetime.fromisoformat(packet['timestamp'])):
                nightMacs[packet['mac2']]=True
        
        filteredData=[packet for packet in data if packet['mac2'] not in nightMacs]
        return filteredData   


    def __removeMacRedundancies(self,df):
        data=df.copy()
        for roomList in self.contiguousRooms:
            rooms=roomList["list"]
            value=roomList["value"]
            rule=str(value)+"Min"
            mask=(data['room'].isin(rooms))
            roomsDataframe=data.loc[mask]
            timeseries=self.__timeseries(roomsDataframe,rule)
            print(timeseries)
            for i in timeseries.index:
                print(i)
                now=(roomsDataframe['date']>=i)&((roomsDataframe['date']<i+timedelta(minutes=value)))
                macs={}
                dataframe=roomsDataframe.loc[now]
                for i in dataframe.index:
                    mac = dataframe['mac2'][i]
                    if mac in macs: 
                        continue
                    else:
                        room = None
                        macs[mac]=True
                        rows = dataframe.loc[dataframe['mac2'] == mac]
                        rssi = rows.rssi.max()
                        if rows.room.nunique() != 1:
                            rooms = rows.loc[rows['rssi'] == rssi]
                            room = rooms.room.values[0]
                            rows=rows.loc[rows["room"]!=room]
                            data.drop(rows.index,inplace=True)
        return data
        

    def addRooms(self,path):
        jsonFile=self.__parseJson(path)
        self.rooms=jsonFile["rooms"]
        self.contiguousRooms=jsonFile["contiguousRooms"]


    def addMacPrefixes(self,path):
        self.macPrefixes=self.__parseJson(path)

    def setNightTime(self,start,end):
        self.nightTimeEnd=end
        self.nightTimeStart=start

    def addDump(self,path):
        data=self.__parseJsonl(path)
        data=self.__filterMac(data)
        data=self.__removeNightTime(data)
        data=self.__removeDuplicate(data)
        tmpDF=pd.DataFrame(data)
        tmpDF=self.__convertTimeStamp(tmpDF)
        #tmpDF['date']=pd.to_datetime(tmpDF['date'])
        self.dataFrame=self.dataFrame.append(tmpDF)
        self.dataFrame.drop_duplicates()

    def setMinuteGranularity(self,minutes):
        if(minutes<=0) :
            raise ValueError("not a valid numerical value")
        self.resampleRule=str(minutes)+"Min"

    def getRooms(self,*args):
        newDf=self.dataFrame[ self.dataFrame['room'].isin(args) ]
        return self.__child(newDf)

    def getInRange(self,start,end):
        mask=(self.dataFrame['date']>=start) & (self.dataFrame['date']<=end)
        newDf=self.dataFrame.loc[mask]
        newDf=self.__removeMacRedundancies(newDf)
        return self.__child(newDf)
    
    @staticmethod
    def __timeseries(dataFrame,rule):
        timeseries=dataFrame.drop(['channel', 'mac1','mac3', 'mac4','scanner_id', 'subtype','type'], axis = 1)
        timeseries=timeseries.groupby(['date','mac2'])['mac2'].nunique()
        s = pd.DataFrame(timeseries)
        s = s.rename(columns={'mac2':'mac'})
        s = s.reset_index(level=[1])
        s = s.drop('mac', axis = 1)
        resampled = s.resample(rule).nunique()
        return resampled

    def getTimeSeries(self):
        resampled=self.__timeseries(self.dataFrame,self.resampleRule)
        return resampled.T.squeeze()




        


    
        
        







