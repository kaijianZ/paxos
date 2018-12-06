from .RadioSend import *
from .ElectionManager import *

class CommandProcessor:
    def __init__(self,hostname):
        self.hostname = hostname
        index, self.MaxIndex = findIndexFromTXTFile(hostname)
        if index < 0:
            raise ValueError("Can not find the hostname in knownhosts_udp.txt")
        self.rs = RadioSend(index,hostname)
        self.em = ElectionManager(hostname,self.rs)

    def processSCHEDULE(self, userInput):
        return ""

    def processCANCEL(self, userInput):
        return ""

    def processVIEW(self):
        return ""

    def processMYVIEW(self):
        return ""

    def processLOG(self):
        return ""

    def processLEADER(self):
        return self.em.getLeader()

    def processRECEIVE_create(self, inputStr):
        return ""

    def processRECEIVE_cancel(self, inputStr):
        return ""

    # heartbeat
    def processHEARTBEAT(self, inputStr):
        self.em.recvHeartbeat(inputStr)
        return ""

    def processHEARTBEAT_reply(self, inputStr):
        self.em.recvHeartbeat_reply(inputStr)
        return ""

    def processHEARTBEAT_check(self, inputStr):
        self.em.checkHeartbeat(inputStr)
        return ""

    # election
    def processELECTION_start(self, inputStr):
        self.em.recvElection(inputStr)
        return ""

    def processELECTION_alive(self, inputStr):
        self.em.recvElection_reply(inputStr)
        return ""

    def processELECTION_victory(self, inputStr):
        self.em.recvVictory(inputStr)
        return ""

#==============================================================================
#                               Helpers
#==============================================================================

# return index representing line number in TXT
# return -1 when no data inside txt matches given hostname
def findIndexFromTXTFile(hostname):
    index = -1
    counter = 0
    with open("knownhosts_udp.txt") as fp:
        line = fp.readline()
        while line:
            siteLines = line.strip('\n').split(' ')
            if hostname == siteLines[0]:
                index = counter
            counter += 1
            line = fp.readline()
    return index, counter
