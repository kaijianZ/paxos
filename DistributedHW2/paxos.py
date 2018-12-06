import pickle, math
import collections
from meeting import *
import random
from RadioSend import *
from threading import RLock, Timer
lock = RLock()

class Prepare:
    def __init__(self, logNum, proposeNum, senderHost):
        self.logNum = logNum
        self.proposeNum = proposeNum
        self.senderHost = senderHost

class Promise:
    def __init__(self, logNum, proposeNum, accNum, accVal):
        self.logNum = logNum
        self.proposeNum = proposeNum
        self.accNum = accNum
        self.accVal = accVal

class AcptReq:
    def __init__(self, logNum, accNum, accVal, senderHost):
        self.logNum = logNum
        self.accNum = accNum
        self.accVal = accVal
        self.senderHost = senderHost

class Accept:
    def __init__(self, logNum, accNum, accVal):
        self.logNum = logNum
        self.accNum = accNum
        self.accVal = accVal

class Commit:
    def __init__(self, logNum, accVal):
        self.logNum = logNum
        self.accVal = accVal


def getProposeNum(counter, index):
    return int(str(counter) + str(index))


class Synod:
    def __init__(self, logNum, sender, proposeVal: Log, trialNum):
        self.trialNum = trialNum
        self.logNum = logNum
        self.maxPrepare = 0
        self.counter = 0
        self.proposeVal = proposeVal
        self.originProposeVal = proposeVal
        self.proposeCounter = 0
        self.accNum = 0
        self.accVal = None
        self.accepted = False
        self.promises = {}
        self.accepts = collections.Counter()
        self.sender = sender
        self.majorityNum = math.ceil(sender.maxIndex/2) + 1

    def prepare_timeout(self, proposeNum):
        lock.acquire()

        if proposeNum not in self.promises.keys():
            self.P_prepare()

        lock.release()

    def accept_timeout(self, proposeNum):
        lock.acquire()

        if self.accepts[proposeNum] < self.majorityNum:
            self.P_prepare()

        lock.release()

    def P_prepare(self):
        lock.acquire()

        if self.proposeCounter == self.trialNum:
            self.fail()
            return

        self.proposeCounter += 1
        self.counter += 1
        proposeNum = getProposeNum(self.counter, self.sender.index)
        msg = Prepare(self.logNum, proposeNum,
                                            self.sender.HOSTNAME)
        self.sender.sendMsgToALL('node', msg)

        lock.release()

        t = Timer(0.05, self.prepare_timeout, [proposeNum])
        t.start()

    def A_promise(self, msg: Prepare):
        lock.acquire()

        senderHost = msg.senderHost
        if msg.proposeNum > self.maxPrepare:
            self.maxPrepare = msg.proposeNum
            msg = Promise(msg.logNum, msg.proposeNum,
                  0 if self.accVal is None else self.accNum, self.accVal)
            self.sender.sendMsg(senderHost, 'node', msg)

        lock.release()

    def P_request(self, msg: Promise):
        lock.acquire()

        #self.promises.get(msg.proposeNum, []).append((msg.accNum, msg.accVal))
        if msg.proposeNum not in self.promises:
            self.promises[msg.proposeNum] = []
        self.promises[msg.proposeNum].append((msg.accNum, msg.accVal))

        print(self.promises)
        if len(self.promises[msg.proposeNum]) >= self.majorityNum:
            value = sorted(self.promises[msg.proposeNum], key=lambda x: x[0],
                                                            reverse=True)[0][1]

            self.proposeVal = self.proposeVal if len(list(filter(lambda x: x[1]
                   is not None, self.promises[msg.proposeNum]))) == 0 else value

            msg = AcptReq(msg.logNum, msg.proposeNum, self.proposeVal,
                                                      self.sender.HOSTNAME)
            self.sender.sendMsgToALL('node', msg)

        lock.release()
        t = Timer(0.05, self.accept_timeout, [msg.proposeNum])
        t.start()


    def A_accept(self, msg: AcptReq):
        lock.acquire()

        senderHost = msg.senderHost
        if msg.proposeNum >= self.maxPrepare:
            self.accNum = msg.proposeNum
            self.accVal = msg.accVal
            self.maxPrepare = msg.proposeNum
            msg = Accept(msg.logNum, msg.accNum, msg.accVal)
            self.sender.sendMsg(senderHost, 'node', msg)

        lock.release()

    def P_commit(self, msg: Accept):
        lock.acquire()

        self.accepts[msg.accNum] += 1
        assert(msg.accVal == self.proposeVal)
        if self.accepts[msg.accNum] >= self.majorityNum:
            self.accepted = True
            if self.originProposeVal == self.proposeVal:
                self.success()
            msg = Commit(self.logNum, msg.accVal)
            self.sender.sendMsgToALL('node', msg)

        lock.release()

    def success(self):
        if self.originProposeVal.op == 'schedule':
            print('Meeting', self.originProposeVal.value.name, 'scheduled.')
        else:
            print('Meeting', self.originProposeVal.value.name, 'cancelled.')

    def fail(self):
        if self.originProposeVal.op == 'schedule':
            print('Unable to schedule meeting',
                            self.originProposeVal.value.name + '.')
        else:
            print('Unable to cancel meeting',
                            self.originProposeVal.value.name + '.')

class Paxos:
    def __init__(self, logSize: int, sender: RadioSend):
        self.log = [None] * logSize
        self.logSynod = [None] * logSize
        self.lastAvailablelogNum = 0
        self.calender = {} # K: event name, V: event
        self.sender = sender

    def view(self):
        ans = ''
        for meeting in sorted_view(self.calender.values()):
            # print(meeting)f
            ans += meeting
        return ans


    def myview(self):
        ans = ''
        for meeting in sorted_view(filter_by_participants(
                                   self.calender.values(), self.sender.HOSTNAME)):
            # print(meeting)
            ans += meeting
        return ans

    def addLog(self, msg: Commit):
        self.log[msg.logNum] = msg.accVal
        if msg.accVal.op == 'schedule':
            self.calender[msg.accVal.value.name] = msg.accVal.value
        else:
            del self.calender[msg.accVal.value.name]
        self.lastAvailablelogNum = max(self.lastAvailablelogNum, msg.logNum + 1)



    def learnVal(self, logNum):
        if self.logSynod[logNum] is None:
            self.logSynod[logNum] = Synod(logNum, self.sender, None, 100)

        self.logSynod[logNum].trialNum = 100
        self.logSynod[logNum].P_prepare()

    def recvAccept(self, msg: Accept):
        self.logSynod[msg.logNum].P_commit(msg)
        if self.logSynod[msg.logNum].accepted:
            self.addLog(Commit(msg.logNum, msg.accVal))


    def msgParser(self, msg):
        if isinstance(msg, Prepare):
            self.logSynod[msg.logNum] = Synod(msg.logNum, self.sender, None, 3)
            self.logSynod[msg.logNum].A_promise(msg)
        elif isinstance(msg, Promise):
            self.logSynod[msg.logNum].P_request(msg)
        elif isinstance(msg, AcptReq):
            self.logSynod[msg.logNum].A_accept(msg)
        elif isinstance(msg, Accept):
            self.recvAccept(msg)
        elif isinstance(msg, Commit):
            self.addLog(msg)
        return ''

    def insert(self, meeting: Meeting, learn: bool):
        if self.learnVals(learn):
            t = Timer(0.1, self.insert, [meeting, False])
            t.start()
        else:
            if ok_to_schedule(self.calender, meeting):
                self.logSynod[self.lastAvailablelogNum] = Synod(self.lastAvailablelogNum,
                        self.sender, Log('schedule', meeting), 3)
                self.logSynod[self.lastAvailablelogNum].P_prepare()
            else:
                print('Unable to schedule meeting', meeting.name + '.')

    def learnVals(self, learn: bool): # return T if hole exists, else F
        for i in range(self.lastAvailablelogNum):
            if self.log[i] is None:
                if learn:
                    self.learnVal(i)
        else:
            return False
        return True

    def delete(self, meeting, learn: bool):
        if self.learnVals(learn):
            t = Timer(0.1, self.delete, [meeting, False])
            t.start()
        else:
            if meeting in self.calender:
                self.logSynod[self.lastAvailablelogNum] = Synod(self.lastAvailablelogNum,
                        self.sender, Log('cancel', meeting), 3)
                self.logSynod[self.lastAvailablelogNum].P_prepare()
            else:
                print('Unable to cancel meeting', meeting + '.')

# class normalPaxos()


