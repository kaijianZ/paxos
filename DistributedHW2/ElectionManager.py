from datetime import datetime
import json

MAX_HEARTBEAT_WAIT = 5

class ElectionManager:
    def __init__(self,hostname,rs):
        self.hostname = hostname
        self.rs = rs
        self.nodeStatus = self.readTXTFileForEM()
        heartbeatDict = {}
        self.leaderHostname = hostname
        for key in self.nodeStatus.keys():
            if key != hostname:
                self.sendHeartbeat(key)

    def getLeader(self):
        return self.leaderHostname

#==============================================================================
#                               Heartbeats
#==============================================================================
    # used to send heartbeat request to a receiver
    def sendHeartbeat(self,targetHostname):
        textObj = {"senderHostname":self.hostname}
        textStr = json.dumps(textObj)
        self.rs.sendMsg(targetHostname,"heartbeat",textStr)
        self.rs.sendMsg(self.hostname,"heartbeat-check",textStr,MAX_HEARTBEAT_WAIT)

    # used to send heartbeat request to a receiver
    def checkHeartbeat(self,inputStr):
        textObj = json.loads(inputStr)
        targetHostname = textObj["senderHostname"]
        if not self.checkAlive(targetHostname):
            print("node: "+targetHostname+" is dead")
            # TODO: dead node, do sth
        else:
            print("node: "+targetHostname+" is alive")
            sendHeartbeat(targetHostname)

    # when receiving heartbeat request, reply alive
    def recvHeartbeat(self,inputStr):
        textObj = json.loads(inputStr)
        senderHostname = textObj["senderHostname"]
        self.rs.sendMsg(targetHostname,"heartbeat-reply",textStr)
        # TODO: can I optimize here by updating the last
        # transmission time with sender? less message will be sent

    # when receiving heartbeat request, reply alive
    def recvHeartbeat_reply(self,inputStr):
        textObj = json.loads(inputStr)
        senderHostname = textObj["senderHostname"]
        self.nodeStatus[senderHostname]["lastHeartbeat"] = datetime.now()

#==============================================================================
#                               Elections
#==============================================================================

    # send election message to all nodes with higher priorities
    def sendElectionToALL(self):
        for key in self.nodeStatus.keys():
            if key > self.hostname:
                self.sendElection(key)

    # send election message to a node
    def sendElection(self,targetHostname):
        self.rs.sendMsg(targetHostname,"election","")

    # send election message to a node
    def recvElection(self,inputStr):
        pass

#==============================================================================
#                               Helpers
#==============================================================================

    def checkAlive(self,targetHostname):
        currentTime = datetime.now()
        lastHeartbeat = self.nodeStatus[targetHostname]["lastHeartbeat"]
        timeDifference = (currentTime - lastHeartbeat).total_seconds()
        if timeDifference > MAX_HEARTBEAT_WAIT:
            return False
        else:
            return True

    def readTXTFileForEM(self):
        sitedict = {}
        with open("knownhosts_udp.txt") as fp:
            line = fp.readline()
            while line:
                siteLines = line.strip('\n').split(' ')
                # initialize as 946702800 <--> 2000-01-01T06:00:00+01:00
                sitedict[siteLines[0]] = {  "lastHeartbeat":datetime.fromtimestamp(946702800),
                                            "status":"dead"}
                line = fp.readline()
        return sitedict
