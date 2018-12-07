from RadioSend import *
from ElectionManager import *
from paxos import *
from meeting import *


class CommandProcessor:
    def __init__(self, hostname):
        self.hostname = hostname
        index, self.MaxIndex = findIndexFromTXTFile(hostname)
        if index < 0:
            raise ValueError("Can not find the hostname in knownhosts_udp.txt")
        self.rs = RadioSend(index, hostname)
        self.em = ElectionManager(hostname, self.rs)
        self.pa = Paxos(10000, self.rs)

    def processSCHEDULE(self, line):
        line = line.split(' ')
        op = line[0]
        name = line[1]
        day = datetime.strptime(line[2], "%m/%d/%Y").date()
        start = datetime.strptime(line[3], "%H:%M").time()
        end = datetime.strptime(line[4], "%H:%M").time()
        participants = line[5].split(',')

        new_meeting = Meeting(name, day, start, end, participants)
        self.pa.insert(new_meeting, True)
        return ""

    def processCANCEL(self, userInput):
        line = userInput.split(' ')
        name = line[1]
        self.pa.delete(name, True)
        return ""

    def processVIEW(self):
        return self.pa.view()

    def processMYVIEW(self):
        return self.pa.myview()

    def processLOG(self):
        ans = ''
        for l in self.pa.log[:self.pa.lastAvailablelogNum]:
            ans += str(l) + '\n'
        return ans.rstrip('\n')

    def processCHECKPOINT(self):
        return self.pa.viewCheckPoint()

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


# ==============================================================================
#                               Helpers
# ==============================================================================

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
