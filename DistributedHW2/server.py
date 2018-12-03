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
    text = strObj["text"]
    if command == "schedule":
        return CP.processSCHEDULE(text)
    elif command == "cancel":
        return CP.processCANCEL(text)
    elif command == "view":
        return CP.processVIEW()
    elif command == "myview":
        return CP.processMYVIEW()
    elif command == "log":
        return CP.processLOG()
    elif command == "receiveCreate":
        return CP.processRECEIVE_create(text)
    elif command == "receiveCancel":
        return CP.processRECEIVE_cancel(text)
    elif command == "heartbeat":
        return CP.processHEARTBEAT(input)
    elif command == "heartbeat-reply":
        return CP.processHEARTBEAT_REPLY(text)
    elif command == "election-start":
        return CP.processELECTION_start(text)
    elif command == "election-alive":
        return CP.processELECTION_alive(text)
    elif command == "election-victory":
        return CP.processELECTION_victory(text)
    else:
        return "Invalid input\n"

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("---Caught user using Ctrl-C. Terminating the program---")
