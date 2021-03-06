import zmq
import time
import socket


def dataKeeper(NodeIndex, processesIndex, startingPortDatakeeperClient, masterCount, masterIP, datakeeperIP):
    print("Datakeeper index = " + str(processesIndex))

    address = {"ip": "" + datakeeperIP + "", "nodeIndex": NodeIndex,
               "head": True if processesIndex == 0 else False}
    context1 = zmq.Context()
    ipSender = context1.socket(zmq.PUSH)
    ipSender.connect("tcp://" + masterIP + ":%s" % str(17777))
    ipSender.send_pyobj(address)
    #print("Ana datakeeper b3at le ip: tcp://" + masterIP + ":%s" % str(17777))
    context = zmq.Context()
    if processesIndex == 0:
        port = 5556+NodeIndex
        socket = context.socket(zmq.PUB)
        socket.bind("tcp://" + datakeeperIP + ":%s" % str(port))
        start = time.time()
        #testingTimer = time.time()

    # Bind ports of datakeeper to be used with client
    context2 = zmq.Context()
    clientSocket = context2.socket(zmq.PAIR)
    clientSocket.bind("tcp://" + datakeeperIP + ":" +
                      str(int(startingPortDatakeeperClient+processesIndex)))
    clientSocket.RCVTIMEO = 1

    # connect ports of datakeeper to send To Master
    context4 = zmq.Context()
    dksocket = context4.socket(zmq.REQ)  # client
    for i in range(masterCount):  # connect Datakeeper to all Masters sockets
        port = 15000+i
        dksocket.connect("tcp://" + masterIP + ":%s" % port)
    # connect ports of datakeeper to be used with Master
    context3 = zmq.Context()
    masterSocket = context3.socket(zmq.SUB)
    masterSocket.RCVTIMEO = 1

    for i in range(masterCount):  # connect Datakeeper to all Masters sockets
        port = 10000+i
        # hena el mafrood no7ot el ip bta3 el master
        masterSocket.connect("tcp://" + masterIP + ":%s" % port)
    topicfilter = "1"
    masterSocket.setsockopt_string(zmq.SUBSCRIBE, topicfilter)
    print("----------------------------------------------------------------------------------")
    print("-- Datakeeper connected to all master processes successfully (n-replicates) !!! --")
    print("----------------------------------------------------------------------------------")

    while True:
        if processesIndex == 0:
            if (time.time()-start >= 1):
                topic = 1  # topic ( I am Alive messages)
                messagedata = 1  # alive
                ip = datakeeperIP
                socket.send_string("%d %d %s %d %d" % (
                    topic, messagedata, ip, NodeIndex, processesIndex))
                start = time.time()
            # if time.time() - testingTimer >= 3+NodeIndex:
                # break

        # Connection with client
        data = []
        try:
            data = clientSocket.recv_pyobj()
        except zmq.error.Again:
            pass

        # Nreplicates connection with master
        data3 = []
        topic = "0"
        messagedata = [None] * 5
        try:
           # print ("try to recive from master \n")
            data3 = masterSocket.recv_string()
            #print ("recieved from master to srcmachine", data3)
            topic, messagedata[0], messagedata[1], messagedata[2], messagedata[3], messagedata[4] = data3.split(
            )
        except zmq.error.Again:
            pass

        # message from Master to sourceMachine dataKeeper here source machine datakeeper send the video to another data keeper so at machine_to_copy it will get in "client upload" as if a client send this file to it
        if topic == "1" and len(messagedata) == 5:
            if messagedata[2] == "source_machine" and messagedata[3] == "tcp://" + datakeeperIP + ":" and messagedata[4] == str(processesIndex+8000):
                #print("sending to Machine to copy")
                contextt = zmq.Context()
                # Datakeeper-Datakeeper connection
                datakeeperSocket = contextt.socket(zmq.PAIR)
                datakeeperSocket.connect(messagedata[0])
                f = open(messagedata[1], 'rb')
                video = f.read()
                datakeeperSocket.send_pyobj([video, messagedata[1]])
                #print("sent to Machine to copy")
                f.close()
                a = datakeeperSocket.recv()
                # print(a)

                "---------------------------------To handle Source machine busy---------------------------------------"
                tocheck = 3
                ip = messagedata[3]
                port = messagedata[4]
                fileName = "a"
                dksocket.send_string(" %d %s %s %s" %
                                     (tocheck, ip, port, fileName))
                dksocket.recv_string()
                "-------------------------------------------------------------------------------------------------------"
        if len(data) == 2:    # Client upload
            # To download in the same location of the file
            name = data[1].split("/")
            f = open(name[-1], 'wb')
            f.write(data[0])
            f.close()
            print("File uploaded successfully")
            # send to master that it is successfully uploaded
            # --------------------------------------------------------------------------------------
            topic = 1
            messagedata = 2
            fileName = name[-1]
            ip = datakeeperIP
            print(fileName)
            port = str(int(startingPortDatakeeperClient+processesIndex))
            dksocket.send_string("%d %s %s %s" %
                                 (messagedata, ip, port, fileName))
            dksocket.recv()
            # --------------------------------------------------------------------------------------------
            clientSocket.send_string("done recieving")

        elif len(data) == 1:  # Client download
            f = open(data[0], 'rb')
            video = f.read()
            clientSocket.send_pyobj([video, data[0]])
            f.close()

