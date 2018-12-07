import pickle, math
import collections
from meeting import *
import random
from RadioSend import *
from threading import RLock, Timer

LOG_STORAGE = 'log.pkl'
CAL_STORAGE = 'cal.pkl'

lock = RLock()

class LastReq:
    def __init__(self, senderHost):
        self.senderHost = senderHost

class Last:
    def __init__(self, lastNum):
        self.lastNum = lastNum

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
        self.majorityNum = math.ceil(sender.maxIndex / 2) + 1

    def prepare_timeout(self, proposeNum):
        lock.acquire()

        if proposeNum not in self.promises.keys() or len(
                self.promises[proposeNum]) < self.majorityNum:
            self.P_prepare()

        lock.release()

    def accept_timeout(self, proposeNum):
        lock.acquire()

        if self.accepts[proposeNum] < self.majorityNum:
            print('selfaccepts|||||||||||', self.accepts[proposeNum],
                  self.majorityNum)
            self.P_prepare()

        lock.release()

    def P_prepare(self):
        lock.acquire()
        print('prepare', self.proposeVal, self.logNum)

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

        t = Timer(0.2, self.prepare_timeout, [proposeNum])
        t.start()

    def A_promise(self, msg: Prepare):
        lock.acquire()
        senderHost = msg.senderHost
        if msg.proposeNum > self.maxPrepare:
            self.maxPrepare = msg.proposeNum
            msg = Promise(msg.logNum, msg.proposeNum,
                          0 if self.accVal is None else self.accNum,
                          self.accVal)
            self.sender.sendMsg(senderHost, 'node', msg)

        lock.release()

    def P_request(self, msg: Promise):
        lock.acquire()

        # self.promises.get(msg.proposeNum, []).append((msg.accNum, msg.accVal))
        old_proposeNum = msg.proposeNum
        if msg.proposeNum not in self.promises:
            self.promises[msg.proposeNum] = []
        self.promises[msg.proposeNum].append((msg.accNum, msg.accVal))

        if len(self.promises[msg.proposeNum]) == self.majorityNum:
            value = sorted(self.promises[msg.proposeNum], key=lambda x: x[0],
                           reverse=True)[0][1]
            print('request', self.proposeVal)

            self.proposeVal = self.proposeVal if \
                len(list(filter(lambda x: x[1] is not None,
                                self.promises[
                                    msg.proposeNum]))) == 0 else value

            print(self.proposeVal, len(list(filter(lambda x: x[1]
                                                             is not None,
                                                   self.promises[
                                                       msg.proposeNum]))),
                  msg.accNum)

            msg = AcptReq(msg.logNum, msg.proposeNum, self.proposeVal,
                          self.sender.HOSTNAME)
            self.sender.sendMsgToALL('node', msg)
            self.proposeCounter = 0
            t = Timer(0.2, self.accept_timeout, [old_proposeNum])
            t.start()
        lock.release()

    def A_accept(self, msg: AcptReq):
        lock.acquire()

        senderHost = msg.senderHost
        if msg.accNum >= self.maxPrepare:
            self.accNum = msg.accNum
            self.accVal = msg.accVal
            self.maxPrepare = msg.accNum
            msg = Accept(msg.logNum, msg.accNum, msg.accVal)
            self.sender.sendMsg(senderHost, 'node', msg)

        lock.release()

    def P_commit(self, msg: Accept):
        lock.acquire()

        self.accepts[msg.accNum] += 1
        # print(msg.accVal, self.proposeVal, '===========')
        # assert(msg.accVal == self.proposeVal)
        if self.accepts[msg.accNum] >= self.majorityNum:
            self.accepted = True
            if self.originProposeVal == self.proposeVal and self.proposeVal is not None:
                self.success()
            msg = Commit(self.logNum, msg.accVal)
            self.sender.sendMsgToALL('node', msg)

        lock.release()

    def success(self):
        if self.originProposeVal.op == 'schedule':
            print('Meeting', self.originProposeVal.value.name, 'scheduled.')
        else:
            print('Meeting', self.originProposeVal.value, 'cancelled.')

    def fail(self):
        if self.originProposeVal.op == 'schedule':
            print('Unable to schedule meeting',
                  self.originProposeVal.value.name + '.')
        else:
            print('Unable to cancel meeting',
                  self.originProposeVal.value + '.')


class Paxos:
    def __init__(self, logSize: int, sender: RadioSend):
        self.log = self.load_log(logSize)
        self.logSynod = [None] * logSize
        self.lastAvailablelogNum = 0
        self.checkPointNum, self.checkPoint = self.load_cal()
        self.calendar = dict.copy(self.checkPoint)
        self.update_cal(self.calendar, self.checkPointNum,
                        self.lastAvailablelogNum)
        # K: event name, V: event
        self.sender = sender
        self.sender.sendMsgToALL('node', LastReq(self.sender.HOSTNAME))

    def view(self):
        ans = ''
        for meeting in sorted_view(self.calendar.values()):
            # print(meeting)
            ans += str(meeting) + '\n'
        return ans.rstrip('\n')

    def myview(self):
        ans = ''
        for meeting in sorted_view(filter_by_participants(
                self.calendar, self.sender.HOSTNAME)):
            # print(meeting)
            ans += str(meeting) + '\n'
        return ans.rstrip('\n')

    def viewCheckPoint(self):
        ans = ''
        for meeting in sorted_view(self.checkPoint.values()):
            ans += str(meeting) + '\n'
        return ans.rstrip('\n')

    def addLog(self, msg: Commit):
        if self.log[msg.logNum] is not None:
            return
        assert (msg.accVal is not None)
        self.log[msg.logNum] = msg.accVal
        self.dump_log()
        lock.acquire()
        if msg.accVal.op == 'schedule' and msg.logNum >= self.lastAvailablelogNum:
            self.calendar[msg.accVal.value.name] = msg.accVal.value
        elif msg.logNum >= self.lastAvailablelogNum:
            del self.calendar[msg.accVal.value]
        self.lastAvailablelogNum = max(self.lastAvailablelogNum, msg.logNum + 1)
        if self.lastAvailablelogNum - self.checkPointNum >= 5 and not self.learnVals(False):
            self.update_cal(self.checkPoint, self.checkPointNum, self.lastAvailablelogNum - self.lastAvailablelogNum % 5)
            self.checkPointNum = self.lastAvailablelogNum - self.lastAvailablelogNum % 5
            self.dump_cal()

        if msg.logNum < self.lastAvailablelogNum and not self.learnVals(False):
            self.calendar = dict.copy(self.checkPoint)
            self.update_cal(self.calendar, self.checkPointNum,
                            self.lastAvailablelogNum)

        lock.release()

    def learnVal(self, logNum):
        lock.acquire()
        if self.logSynod[logNum] is None:
            self.logSynod[logNum] = Synod(logNum, self.sender, None, 100)

        self.logSynod[logNum].trialNum = 100
        self.logSynod[logNum].P_prepare()
        lock.release()

    def recvAccept(self, msg: Accept):
        lock.acquire()
        self.logSynod[msg.logNum].P_commit(msg)
        if self.logSynod[msg.logNum].accepted:
            self.addLog(Commit(msg.logNum, msg.accVal))
        lock.release()

    def msgParser(self, msg):
        lock.acquire()
        print('receive', msg)
        if isinstance(msg, Prepare):
            if self.logSynod[msg.logNum] is None:
                self.logSynod[msg.logNum] = Synod(msg.logNum, self.sender, None,
                                                  3)
            self.logSynod[msg.logNum].A_promise(msg)
        elif isinstance(msg, Promise):
            self.logSynod[msg.logNum].P_request(msg)
        elif isinstance(msg, AcptReq):
            self.logSynod[msg.logNum].A_accept(msg)
        elif isinstance(msg, Accept):
            self.recvAccept(msg)
        elif isinstance(msg, Commit):
            self.addLog(msg)
        elif isinstance(msg, LastReq):
            self.sender.sendMsg(msg.senderHost, 'node',
                                Last(self.lastAvailablelogNum))
        elif isinstance(msg, Last):
            self.lastAvailablelogNum = msg.lastNum
            self.learnVals(True)
        else:
            print(msg)
        lock.release()
        return ''

    def insert(self, meeting: Meeting, learn: bool):
        lock.acquire()
        if self.lastAvailablelogNum > 0 and self.learnVals(learn):
            t = Timer(0.2, self.insert, [meeting, False])
            t.start()
        else:
            if ok_to_schedule(self.calendar, meeting):
                print('success--------------')
                print(self.log[:10])
                self.logSynod[self.lastAvailablelogNum] = Synod(
                    self.lastAvailablelogNum,
                    self.sender, Log('schedule', meeting), 3)
                self.logSynod[self.lastAvailablelogNum].P_prepare()
            else:
                print('Unable to schedule meeting', meeting.name + '.')
        lock.release()

    def learnVals(self, learn: bool):  # return T if hole exists, else F
        lock.acquire()
        returnVal = False
        for i in range(self.lastAvailablelogNum):
            if self.log[i] is None:
                returnVal = True
                if learn:
                    self.learnVal(i)
        lock.release()
        print('holes?', returnVal)
        return returnVal

    def delete(self, meeting, learn: bool):
        lock.acquire()
        if self.learnVals(learn):
            t = Timer(0.2, self.delete, [meeting, False])
            t.start()
        else:
            print('success--------------')
            if meeting in self.calendar:
                self.logSynod[self.lastAvailablelogNum] = Synod(
                    self.lastAvailablelogNum,
                    self.sender, Log('cancel', meeting), 3)
                self.logSynod[self.lastAvailablelogNum].P_prepare()
            else:
                print('Unable to cancel meeting', meeting + '.')
        lock.release()

    def dump_log(self):
        with open(LOG_STORAGE, 'wb') as fout:
            pickle.dump(self.log, fout, pickle.HIGHEST_PROTOCOL)

    def load_log(self, logSize):
        if os.path.isfile(LOG_STORAGE) is True:
            with open(LOG_STORAGE, 'rb') as fin:
                return pickle.load(fin)
        else:
            return [None] * logSize

    def dump_cal(self):
        tup = (self.checkPointNum, self.checkPoint)
        with open(CAL_STORAGE, 'wb') as fileout:
            pickle.dump(tup, fileout, pickle.HIGHEST_PROTOCOL)

    def load_cal(self):
        if os.path.isfile(CAL_STORAGE) is True:
            with open(CAL_STORAGE, 'rb') as filein:
                return pickle.load(filein)
        else:
            return (0, {})

    def update_cal(self, calendar, logstart, logend):
        for ind in range(logstart, logend):
            if self.log[ind].op == 'schedule':
                calendar[self.log[ind].value.name] = self.log[ind].value
            else:
                del calendar[self.log[ind].value]
