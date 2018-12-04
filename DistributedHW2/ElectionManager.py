from datetime import datetime
import json
import threading
import time

HEARTBEAT_WAIT = 5
ELECTION_WAIT = 1
VICTORY_WAIT = 1
ALLOWED_TIMER_LATENCY = 0.1

# assume message for this eletion Won't go to next election
# e.g: laggy network, delay the UDP message
class ElectionManager:
    def __init__(self,hostname,rs):
        print("===========Initializing start===========")
        self.hostname = hostname
        self.rs = rs
        self.nodeStatus = self.readTXTFileForEM()
        heartbeatDict = {}
        self.leaderHostname = None
        self.receivedVictory = False
        for key in self.nodeStatus.keys():
            if key != hostname:
                self.sendHeartbeat(key)
        self.sendElectionToALL()
        print("===========Initializing Ends===========")

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
        t = threading.Timer(HEARTBEAT_WAIT,self.checkHeartbeat,[targetHostname])
        t.start()

    # when receiving heartbeat request, reply alive
    def recvHeartbeat(self,inputStr):
        textObj = json.loads(inputStr)
        senderHostname = textObj["senderHostname"]
        textObj2 = {"senderHostname":self.hostname}
        textStr2 = json.dumps(textObj2)
        self.rs.sendMsg(senderHostname,"heartbeat-reply",textStr2)
        if self.nodeStatus[senderHostname]["status"] == False:
            self.nodeStatus[senderHostname]["status"] = True
            self.sendHeartbeat(senderHostname)
        # TODO: can I optimize here by updating the last
        # transmission time with sender? less message will be sent

    # when receiving heartbeat_reply, update with the receiving time
    def recvHeartbeat_reply(self,inputStr):
        textObj = json.loads(inputStr)
        senderHostname = textObj["senderHostname"]
        self.nodeStatus[senderHostname]["lastHeartbeat"] = datetime.now()
        print("HB-reply:"+senderHostname)

    # used to check heartbeat from the hostname
    # if dead, elect new leader if needed
    def checkHeartbeat(self,hostname):
        if not self._checkHeartbeat(hostname):
            print("node: "+hostname+" is dead")
            # if the dead node is the leader, reelect
            self.nodeStatus[hostname]["status"] = False
            if hostname == self.leaderHostname:
                self.sendElectionToALL()
        else:
            print("node: "+hostname+" is alive")
            self.nodeStatus[hostname]["status"] = True
            self.sendHeartbeat(hostname)

#==============================================================================
#                               Elections
#==============================================================================

    # send election message to all nodes with higher priorities
    def sendElectionToALL(self):
        print("sendElectionToALL")
        for key in self.nodeStatus.keys():
            if self.compareNodePriority(key,self.hostname):
                self.sendElection(key)
        # add 0.1 for safety, need to assure it finishes after other threads
        t = threading.Timer(ELECTION_WAIT+ALLOWED_TIMER_LATENCY,self.checkElectionOnALL)
        t.start()

    # send election message to a node
    def sendElection(self,targetHostname):
        print("sendElection to "+str(targetHostname))
        textObj = {"senderHostname":self.hostname}
        textStr = json.dumps(textObj)
        self.rs.sendMsg(targetHostname,"election-start",textStr)
        t = threading.Timer(ELECTION_WAIT,self.checkElection,[targetHostname])
        t.start()

    # received election message
    # will reply (alive)
    def recvElection(self,inputStr):
        textObj = json.loads(inputStr)
        senderHostname = textObj["senderHostname"]
        print("recvElection from "+str(senderHostname))
        textObj2 = {"senderHostname":self.hostname}
        textStr2 = json.dumps(textObj2)
        print("\tsend election-reply back")
        self.rs.sendMsg(senderHostname,"election-reply",textStr2)
        # send election to nodes higher-level than myself
        self.sendElectionToALL()

    # received election-reply (alive) message
    def recvElection_reply(self,inputStr):
        textObj = json.loads(inputStr)
        senderHostname = textObj["senderHostname"]
        print("recvElection_reply from "+str(senderHostname))
        self.nodeStatus[senderHostname]["lastElection"] = datetime.now()

    # check whether the given node replied alive in time
    # if yes, mark the node ready for leader position
    # if not, mark the node NOT ready for leader position
    def checkElection(self,hostname):
        if self._checkElection(hostname):
            print("checkElection: mark "+str(hostname)+" as True")
            self.nodeStatus[hostname]["leaderAvailable"] = True
        else:
            print("checkElection: mark "+str(hostname)+" as False")
            self.nodeStatus[hostname]["leaderAvailable"] = False

    # check whether any node replied alive in time
    # if yes, shut up and wait for victory till timedout
    # if no, send victory to everyone
    def checkElectionOnALL(self):
        print("checkElectionOnALL")
        for key in self.nodeStatus.keys():
            if self.nodeStatus[key]["leaderAvailable"] == True:
                self.victory = None
                t = threading.Timer(VICTORY_WAIT,self.checkVictory)
                t.start()
                # another higher-level and alive node
                # wait for his/others victory till timieout
                return
        # all nodes are False
        # it's my VICTORY
        print("timeout on alive")
        self.sendVictoryToALL()

#==============================================================================
#                               Victory
#==============================================================================

    def sendVictoryToALL(self):
        print("sendVictoryToALL")
        for key in self.nodeStatus.keys():
            textObj = {"senderHostname":self.hostname}
            textStr = json.dumps(textObj)
            self.rs.sendMsg(key,"election-victory",textStr)

    def recvVictory(self,inputStr):
        print("recvVictory")
        textObj = json.loads(inputStr)
        senderHostname = textObj["senderHostname"]
        print("\told leader was "+str(self.leaderHostname))
        self.leaderHostname = senderHostname
        self.receivedVictory = True
        print("\tnew leader is "+self.leaderHostname)

    def checkVictory(self):

        if self.receivedVictory == False:
            # leader timeout his victory, reelect one
            print("checkVictory-timeout on victory")
            self.sendElectionToALL()
        else:
            # the leader calimed victory, end the election
            print("checkVictory-found leader")
            self.receivedVictory == False

#==============================================================================
#                               Helpers
#==============================================================================

    def compareNodePriority(self,nameA,nameB):
        if nameA > nameB:
            return True
        else:
            return False

    def _checkHeartbeat(self,targetHostname):
        currentTime = datetime.now()
        lastHeartbeat = self.nodeStatus[targetHostname]["lastHeartbeat"]
        timeDifference = (currentTime - lastHeartbeat).total_seconds()
        if timeDifference > (HEARTBEAT_WAIT+ALLOWED_TIMER_LATENCY):
            return False
        else:
            return True

    def _checkElection(self,targetHostname):
        currentTime = datetime.now()
        lastHeartbeat = self.nodeStatus[targetHostname]["lastElection"]
        timeDifference = (currentTime - lastHeartbeat).total_seconds()
        if timeDifference > (ELECTION_WAIT+ALLOWED_TIMER_LATENCY):
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
                                            "lastElection":datetime.fromtimestamp(946702800),
                                            "leaderAvailable":False,
                                            "status":False}
                line = fp.readline()
        return sitedict
