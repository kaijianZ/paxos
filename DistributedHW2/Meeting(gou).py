from datetime import datetime

class Meeting:
    def __init__(self, name, day,start, end, participants):
        self.name = name
        self.day = day
        self.start = start
        self.end = end
        self.participants = participants

    def toString(self):
        nameStr = self.name + " "
        dayStr = self.day.strftime("%m/%d/%Y ")
        startStr = self.start.strftime("%H:%M ")
        endStr = self.end.strftime("%H:%M ")
        participantStr = ",".join(self.participants)
        return nameStr + dayStr + startStr + endStr + participantStr

#==============================================================================
#                               Helpers
#==============================================================================

def parseDateString2Datetime(dateStr):
    return datetime.strptime(dateStr, '%m/%d/%Y')

def parseTimeString2Datetime(timeStr):
    return datetime.strptime(timeStr, '%H:%M')

def participantStr2List(str):
    strList = str.split(',')
    return strList

def strList2Meeting(userInputList):
    name = userInputList[1]
    day = parseDateString2Datetime(userInputList[2])
    start = parseTimeString2Datetime(userInputList[3])
    end = parseTimeString2Datetime(userInputList[4])
    participants = participantStr2List(userInputList[5])
    return Meeting( name,
                    day,
                    start,
                    end,
                    participants)

def checkMeetingAvailability(meetingA,meetingB):
    # both on same day
    if (meetingA.day == meetingB.day):
        # whether no overlap between meetings
        if (meetingA.end <= meetingB.start):
            # record is earlier than meeting
            return True
        elif (meetingB.end <= meetingA.start):
            # record is later than meeting
            return True
        else:
            return False
    else:
        # no one same day, not possible to have conflict
        return True
