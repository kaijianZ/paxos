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

    def sendMsgToALL(self,message):
        for key in self.sockList:
            self.sendMsg(self.sockList[key][0],message)

    def sendMsg(self,targetHostname,message):
        # targetIndex = self.sitedict[targetHostname]["index"]
        targetAddr = self.sockList[targetHostname]
        print("===================SEND=======================")
        self.sock.sendto(text,targetAddr)

#==============================================================================
#                               Helpers
#==============================================================================

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
