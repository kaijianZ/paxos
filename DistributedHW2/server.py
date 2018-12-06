import select
from socket import *
import sys
import traceback
import json
from .CommandProcessor import *
from .RadioSend import *

BACKLOG_MAX = 5
PACKETSIZE_MAX = 1024
TIMEOUT = 5

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
    CP = CommandProcessor(HOSTNAME)
    data_buffer = bytearray(PACKETSIZE_MAX)
    sys.stdout.flush()

    while True:
        readable, writable, exceptional = select.select([server.fileno()],
                                                        [],
                                                        [])
        data, sender_addr = server.recvfrom(PACKETSIZE_MAX)
        # print(data.decode("utf-8"))
        try:
            ret = processInput(data.decode("utf-8"), CP)
        except Exception as e:
            traceback.print_exc()
            ret = "Internal error"
        if ret == "REMOTE":
            continue
        server.sendto(str.encode(ret),sender_addr)
        sys.stdout.flush()

def processInput(str, CP):
    try:
        strObj = json.loads(str)
        command = strObj["command"]
        # print("/"+command)
    except:
        print("Invalid input: " + str)
        traceback.print_exc()
        return "Invalid input"

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
    elif command == "leader":
        return CP.processLEADER()
    elif command == "receiveCreate":
        return CP.processRECEIVE_create(text)
    elif command == "receiveCancel":
        return CP.processRECEIVE_cancel(text)
    elif command == "heartbeat":
        return CP.processHEARTBEAT(text)
    elif command == "heartbeat-reply":
        return CP.processHEARTBEAT_reply(text)
    elif command == "heartbeat-check":
        return CP.processHEARTBEAT_check(text)
    elif command == "election-start":
        return CP.processELECTION_start(text)
    elif command == "election-reply":
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
