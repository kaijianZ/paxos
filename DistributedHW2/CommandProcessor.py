from CalenderManager import CalenderManager
from Meeting import Meeting, strList2Meeting

class CommandProcessor:
    def __init__(self,hostname):
        index, MaxIndex = findIndexFromTXTFile(hostname)
        if index < 0:
            raise ValueError("Can not find the hostname in knownhosts_udp.txt")
        self.calender = CalenderManager(hostname, index, MaxIndex)

    def processSCHEDULE(self, userInput):
        userInputList = userInput.split(" ")
        if len(userInputList) != 6:
            return "Unable to schedule meeting with UNKNOWN input."
        meeting = strList2Meeting(userInputList)
        noConflict = self.calender.addMeeting(meeting)
        if noConflict:
            return "Meeting " + meeting.name + " scheduled."
        else:
            return "Unable to schedule meeting " + userInputList[1] + "."

    def processCANCEL(self, userInput):
        userInputList = userInput.split(" ")
        if len(userInputList) != 2:
            return "Unable to cancel meeting with UNKNOWN input."
        findMeeting = self.calender.delMeeting(userInputList[1])
        if findMeeting:
            return "Meeting " + userInputList[1] + " cancelled."
        else:
            return "Unable to find meeting " + userInputList[1] + "."

    def processVIEW(self):
        ret = ""
        meetingList = self.calender.listMeeting()
        for meeting in meetingList:
            ret += meeting.toString() + "\n"
        return ret.rstrip()

    def processMYVIEW(self):
        ret = ""
        meetingList = self.calender.listMyMeeting()
        for meeting in meetingList:
            ret += meeting.toString() + "\n"
        return ret.rstrip()

    def processLOG(self):
        ret = ""
        logList = self.calender.listLog()
        print("logLen:"+str(len(logList)))
        for log in logList:
            ret += log.toString() + "\n"
        return ret.rstrip()

    def processRECEIVE_create(self, tStr, npStr, senderIndex):
        print("REMOTE----CREATE")
        self.calender.changeLogStatus(tStr,npStr,senderIndex)
        return "REMOTE"

    def processRECEIVE_cancel(self, tStr, npStr, senderIndex):
        print("REMOTE----CANCEL")
        self.calender.changeLogStatus(tStr,npStr,senderIndex)
        return "REMOTE"

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
