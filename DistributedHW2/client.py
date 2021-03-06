import sys
from socket import *
import pickle
from RadioSend import *

PACKETSIZE_MAX = 1024


def main():
    HOSTNAME = sys.argv[1]
    sitelist, _ = readTXTFile()
    PORT = sitelist[sys.argv[1]]["port"]

    addr = (HOSTNAME, PORT)
    try:
        sock = socket(AF_INET, SOCK_DGRAM)
    except error:
        print("Can not connect to server, %s:%s" % addr)
        sys.exit()
    print("Connected to server, %s:%s" % addr)

    while True:
        try:
            userInput = input()
            userInputObj = str2jsonStr(userInput)
        except ValueError as e:
            print(e)
            continue
        sock.sendto(userInputObj, addr)
        if userInput == "exit":
            break
        reply, _ = sock.recvfrom(PACKETSIZE_MAX)
        print(reply.decode())

def str2jsonStr(str):
    strList = str.split(" ")
    command = strList[0]
    strD = {}
    strD["command"] = ""
    strD["text"] = ""
    if command == "schedule":
        strD["command"] = "schedule"
        strD["text"] = str
    elif command == "cancel":
        strD["command"] = "cancel"
        strD["text"] = str
    elif command == "view":
        strD["command"] = "view"
    elif command == "myview":
        strD["command"] = "myview"
    elif command == "log":
        strD["command"] = "log"
    elif command == "checkpoint":
        strD["command"] = "checkpoint"    
    elif command == "leader":
        strD["command"] = "leader"
    elif command == "exit":
        strD["command"] = "exit"
    else:
        raise ValueError("Invalid input")
    jsonStr = pickle.dumps(strD)
    return jsonStr


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("---Caught user use Ctrl-C. Terminating the program---")
