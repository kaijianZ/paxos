import select
from socket import *
import sys
import traceback
import json
from CommandProcessor import CommandProcessor
from RadioSend import readTXTFile

BACKLOG_MAX = 5
PACKETSIZE_MAX = 1024

def main():
    HOSTNAME = sys.argv[1]
    sitelist,_ = readTXTFile()
    PORT = sitelist[sys.argv[1]]["port"]
    print("Hostname: [" + HOSTNAME + "] on port [" + str(PORT) + "]")

    server = socket(AF_INET, SOCK_DGRAM)
    try:
        server.bind((HOSTNAME, PORT))
    except:
        print("Failed to bind(): server is possibly already running")
        sys.exit(0)
    input = [server]
    CP = CommandProcessor(HOSTNAME)
    sys.stdout.flush()

    while True:
        data, addr = server.recvfrom(PACKETSIZE_MAX)
        try:
            ret = processInput(data.decode("utf-8"), CP)
        except Exception as e:
            traceback.print_exc()
            ret = "Internal error"
        if ret == "REMOTE":
            continue
        server.sendto(str.encode(ret),addr)
        sys.stdout.flush()

def processInput(str, CP):
    try:
        strObj = json.loads(str)
        command = strObj["command"]
    except:
        print("Invalid input: " + str)
        return "Invalid input"

    print("/"+command)
    if command == "schedule":
        input = strObj["text"]
        return CP.processSCHEDULE(input)
    elif command == "cancel":
        input = strObj["text"]
        return CP.processCANCEL(input)
    elif command == "view":
        return CP.processVIEW()
    elif command == "myview":
        return CP.processMYVIEW()
    elif command == "log":
        return CP.processLOG()
    elif command == "receiveCreate":
        tStr = strObj["T"]
        npStr = strObj["NP"]
        senderIndex = strObj["senderIndex"]
        return CP.processRECEIVE_create(tStr, npStr, senderIndex)
    elif command == "receiveCancel":
        tStr = strObj["T"]
        npStr = strObj["NP"]
        senderIndex = strObj["senderIndex"]
        return CP.processRECEIVE_cancel(tStr, npStr, senderIndex)
    else:
        return "Invalid input\n"

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("---Caught user using Ctrl-C. Terminating the program---")
