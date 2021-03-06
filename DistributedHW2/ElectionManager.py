from datetime import datetime
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
        #print("===========Initializing start===========")
        self.hostname = hostname
        self.rs = rs
        self.nodeStatus = self.readTXTFileForEM()
        heartbeatDict = {}
        self.leaderHostname = hostname
        self.receivedVictory = False
        for key in self.nodeStatus.keys():
            if key != hostname:
                self.sendHeartbeat(key)
        self.sendElectionToALL()
        #print("===========Initializing Ends===========")

    def getLeader(self):
        return self.leaderHostname

#==============================================================================
#                               Heartbeats
#==============================================================================
    # used to send heartbeat request to a receiver
    def sendHeartbeat(self,targetHostname):
        textObj = {"senderHostname":self.hostname}
        self.rs.sendMsg(targetHostname,"heartbeat",textObj)
        t = threading.Timer(HEARTBEAT_WAIT,self.checkHeartbeat,[targetHostname])
        t.start()

    # when receiving heartbeat request, reply alive
    def recvHeartbeat(self,textObj):
        senderHostname = textObj["senderHostname"]
        textObj2 = {"senderHostname":self.hostname}
        self.rs.sendMsg(senderHostname,"heartbeat-reply",textObj2)
        if self.nodeStatus[senderHostname]["status"] == False:
            self.nodeStatus[senderHostname]["status"] = True
            self.sendHeartbeat(senderHostname)
        # TODO: can I optimize here by updating the last
        # transmission time with sender? less message will be sent

    # when receiving heartbeat_reply, update with the receiving time
    def recvHeartbeat_reply(self,textObj):
        senderHostname = textObj["senderHostname"]
        self.nodeStatus[senderHostname]["lastHeartbeat"] = datetime.now()
        #print("HB-reply:"+senderHostname)

    # used to check heartbeat from the hostname
    # if dead, elect new leader if needed
    def checkHeartbeat(self,hostname):
        if not self._checkHeartbeat(hostname):
            #print("node: "+hostname+" is dead")
            # if the dead node is the leader, reelect
            self.nodeStatus[hostname]["status"] = False
            if hostname == self.leaderHostname:
                self.sendElectionToALL()
        else:
            #print("node: "+hostname+" is alive")
            self.nodeStatus[hostname]["status"] = True
            # optimization
            # only send heartbeat to leader, it is the only node matters
            if hostname == self.leaderHostname:
                self.sendHeartbeat(hostname)

#==============================================================================
#                               Elections
#==============================================================================

    # send election message to all nodes with higher priorities
    def sendElectionToALL(self):
        #print("sendElectionToALL")
        # optimization
        # if this node is the highest-value node, ignore election and send victory
        highestHostname = max(list(self.nodeStatus.keys()))
        if self.hostname == highestHostname:
            self.sendVictoryToALL()
            return

        for key in self.nodeStatus.keys():
            if key > self.hostname:
                self.sendElection(key)
        # add 0.1 for safety, need to assure it finishes after other threads
        t = threading.Timer(ELECTION_WAIT+ALLOWED_TIMER_LATENCY,self.checkElectionOnALL)
        t.start()

    # send election message to a node
    def sendElection(self,targetHostname):
        #print("sendElection to "+str(targetHostname))
        textObj = {"senderHostname":self.hostname}
        self.rs.sendMsg(targetHostname,"election-start",textObj)
        t = threading.Timer(ELECTION_WAIT,self.checkElection,[targetHostname])
        t.start()

    # received election message
    # will reply (alive)
    def recvElection(self,textObj):
        senderHostname = textObj["senderHostname"]
        #print("recvElection from "+str(senderHostname))
        textObj2 = {"senderHostname":self.hostname}
        #print("\tsend election-reply back")
        self.rs.sendMsg(senderHostname,"election-reply",textObj2)
        # send election to nodes higher-level than myself
        self.sendElectionToALL()

    # received election-reply (alive) message
    def recvElection_reply(self,textObj):
        senderHostname = textObj["senderHostname"]
        #print("recvElection_reply from "+str(senderHostname))
        self.nodeStatus[senderHostname]["lastElection"] = datetime.now()

    # check whether the given node replied alive in time
    # if yes, mark the node ready for leader position
    # if not, mark the node NOT ready for leader position
    def checkElection(self,hostname):
        if self._checkElection(hostname):
            #print("checkElection: mark "+str(hostname)+" as True")
            self.nodeStatus[hostname]["leaderAvailable"] = True
        else:
            #print("checkElection: mark "+str(hostname)+" as False")
            self.nodeStatus[hostname]["leaderAvailable"] = False

    # check whether any node replied alive in time
    # if yes, shut up and wait for victory till timedout
    # if no, send victory to everyone
    def checkElectionOnALL(self):
        #print("checkElectionOnALL")
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
        #print("timeout on alive")
        self.sendVictoryToALL()

#==============================================================================
#                               Victory
#==============================================================================

    def sendVictoryToALL(self):
        #print("sendVictoryToALL")
        for key in self.nodeStatus.keys():
            textObj = {"senderHostname":self.hostname}
            self.rs.sendMsg(key,"election-victory",textObj)

    def recvVictory(self,textObj):
        #print("recvVictory")
        senderHostname = textObj["senderHostname"]
        # #print("\told leader was "+str(self.leaderHostname))
        self.leaderHostname = senderHostname
        self.receivedVictory = True
        # #print("\tnew leader is "+self.leaderHostname)

    def checkVictory(self):
        if self.receivedVictory == False:
            # leader timeout his victory, reelect one
            # #print("checkVictory-timeout on victory")
            self.sendElectionToALL()
        else:
            # the leader calimed victory, end the election
            # #print("checkVictory-found leader")
            self.receivedVictory == False

#==============================================================================
#                               Helpers
#==============================================================================

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
