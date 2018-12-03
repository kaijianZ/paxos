from datetime import datetime

MAX_HEARTBEAT_WAIT = 5

class ElectionManager:
    def __init__(self,hostname,rs):
        self.hostname = hostname
        self.rs = rs
        self.nodeStatus = readTXTFileForEM()
        heartbeatDict = {}
        self.leaderHostname = hostname

    def getLeader(self):
        return self.leaderHostname

    # used when no heartbeat received in designated time
    def checkAlive(self):
        for key in self.nodeStatus.keys():
            currentTime = datetime.now()
            lastTime = self.nodeStatus[key]["lastHeartbeat"]
            timeDifference = (currentTime - lastTime).total_seconds()
            if timeDifference > MAX_HEARTBEAT_WAIT:
                # mark this node as dead
                self.nodeStatus[key]["status"] = "dead"
                # TODO: do leader election if necessary

    # used to send heartbeat request to everyone
    def sendHeartbeatToALL(self):
        for key in self.nodeStatus.keys():
            self.sendHeartbeat(key)

    # used to send heartbeat request to a receiver
    def sendHeartbeat(self,targetHostname):
        text = {"senderHostname":self.hostname}
        # TODO: dump text into string
        rs.sendMsg(targetHostname,"heartbeat",textStr)

    # used to recv heartbeat from one sender
    def recvHeartbeat(self,inputStr):
        # TODO: dump string into dict
        senderHostname = obj["senderHostname"]
        self.nodeStatus[senderHostname]["lastHeartbeat"] = datetime.now()
        if self.nodeStatus[senderHostname]["status"] == "dead":
            # TODO: do leader election if necessary
            pass
        self.nodeStatus[senderHostname]["status"] = alive

#==============================================================================
#                               Helpers
#==============================================================================

def readTXTFileForEM():
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
