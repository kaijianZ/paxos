from socket import *
from Meeting import Meeting
import json

class RadioSend:
    def __init__(self,index,hostname):
        self.sitedict, self.maxIndex = readTXTFile()
        self.HOSTNAME = hostname
        self.PORT = self.sitedict[hostname]["port"]
        self.index = index
        siteKeylist = list(self.sitedict.keys())
        self.sock = tmp_sock = socket(AF_INET, SOCK_DGRAM)
        self.sockList = {}
        for i in range(0,self.maxIndex):
            tmp_hostname = siteKeylist[i]
            tmp_port = self.sitedict[tmp_hostname]["port"]
            self.sockList[tmp_hostname] = (tmp_hostname,tmp_port)

    def sendCreateMsg(self,targetHostname,meeting,T,logs):
        targetIndex = self.sitedict[targetHostname]["index"]
        targetAddr = self.sockList[targetHostname]

        print("===================SEND=======================")
        print("self.T:"+str(T))
        print("Each self.pl:")
        NP = []
        for log in logs:
            print(log.name+"--"+str(targetIndex)+str(log.index)+"--"+str(T[targetIndex][log.index])+">="+str(log.counter))
            if not hasRec(T,log,targetIndex):
                NP.append(log.toMsgString())

        tStr= json.dumps(T)
        npStr= json.dumps(NP)

        print("tStr:"+tStr)
        print("npStr:"+npStr)

        payload = {"command":"receiveCreate", "T": tStr, "NP": npStr, "senderIndex": self.index}
        jsonStr = json.dumps(payload)
        self.sock.sendto(jsonStr.encode(),targetAddr)

    def sendCancelMsg(self,targetHostname,meetingName,T,logs):
        targetIndex = self.sitedict[targetHostname]["index"]
        targetAddr = self.sockList[targetHostname]

        print("===================SEND=======================")
        print("self.T:"+str(T))
        print("Each self.pl:")
        NP = []
        for log in logs:
            print(log.name+"--"+str(targetIndex)+str(log.index)+"--"+str(T[targetIndex][log.index])+">="+str(log.counter))
            if not hasRec(T,log,targetIndex):
                NP.append(log.toMsgString())

        tStr= json.dumps(T)
        npStr= json.dumps(NP)
        print("tStr:"+tStr)
        print("npStr:"+npStr)

        payload = {"command":"receiveCancel", "T": tStr, "NP": npStr, "senderIndex": self.index}
        jsonStr = json.dumps(payload)
        self.sock.sendto(jsonStr.encode(),targetAddr)

#==============================================================================
#                               Helpers
#==============================================================================

def hasRec(T,log,k):
    return T[k][log.index] >= log.counter

def readTXTFile():
    sitedict = {}
    with open("knownhosts_udp.txt") as fp:
        line = fp.readline()
        counter = 0
        while line:
            siteLines = line.strip('\n').split(' ')
            sitedict[siteLines[0]] = {"port":int(siteLines[1]), "index":counter}
            line = fp.readline()
            counter += 1
    return sitedict, counter
