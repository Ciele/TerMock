import sys
import socket
import time
import datetime
import threading
import random
import asyncio
import schedule

"""
_logoMsg = "*VK201580000000000000,AB#"
_helloMsg = "*VK201580000000000000,AH#"
*VK201580000000000000,AB&A1450172236915411403232860012290518&V1000000000000&B0100000000&W00&G000030&M350&N21&O1400#
*VK201580000000000000,AH&A1450172236915411403232860012290518&V1000000000000&B0100000000&W00&G000030&M350&N21&O1400#
"""


class mythread(threading.Thread, object):

    #server = "192.168.2.181"
    #port = 9876

    server = "192.168.30.97"
    port = 8080

    #server = "183.62.157.202"
    #port = 20243

    randmDurLogin = 10  # 随机10秒

    sayHelloTime = 30  # 秒

    DEBUG = True  # True:all, False:使用 LOGLEVEL 定义
    LOGLEVEL = 2  # 0:all(默认), 1:多, 2:少

    TOTAL = 0
    CONNECTED = 0
    SENDED = 0
    LOGIN = 0
    RETRAY = 0
    RECIEVE_CMD_TOTAL = 0
    RECIEVE_CMD_NEED_ANSWER = 0
    RECIEVE_CMD_NONEED_ANSWER = 0
    ANSWER_CMD_TOTAL = 0

    IS_T19 = False

    def __init__(self, imei, server=server, port=port):
        threading.Thread.__init__(self)
        self.imei = imei
        self.server = server
        self.port = port
        self.socket = ""
        self.timer = ""
        self.connectedTime = ""
        self.sendLoginTime = ""
        self.recieveTime = ""
        self.connected = False
        self.sayHelloTime = mythread.sayHelloTime
        self.logined = False
        self.isStopSayHello = False
        threadLock.acquire()
        mythread.TOTAL += 1
        threadLock.release()

    def connect(self):
        while True:
            try:
                self.socket.close()
                self.socket = ""
            except:
                pass

            mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            stopTime = random.random() * mythread.randmDurLogin
            self.printl("随机暂停 {}秒".format(stopTime))
            time.sleep(stopTime)
            self.printl("正在连接到 {}:{}".format(self.server, self.port))
            try:
                mysock.connect((self.server, self.port))
            except:
                if self.connected:
                    threadLock.acquire()
                    mythread.CONNECTED -= 1
                    threadLock.release()
                    self.connected = False

                threadLock.acquire()
                mythread.RETRAY += 1
                threadLock.release()

                self.printl("Unexpected error:{}".format(sys.exc_info()), 2)
                self.printl('5秒后重试...', 1)
                time.sleep(5)

            else:
                self.printl('连接成功')
                self.printl('mysock:{}'.format(mysock))
                self.socket = mysock

                self.connectedTime = self.getCurrentTime()
                if not self.connected:
                    threadLock.acquire()
                    mythread.CONNECTED += 1
                    threadLock.release()
                    self.connected = True

                return mysock

    def login(self):
        logMsg = "*VK201{},AB&A1450172236915411403232860012290518&V1000000000000&B0100000000&W00&G000030&M350&N21&O1400#".format(
            self.imei)
        self.printl('登录中...')
        self.sendLoginTime = self.getCurrentTime()
        return self.sendSocketMsg(logMsg, printLevel=2)

    def isSayHello(self, recvMsg):
        return (recvMsg[5:8] == 'YAH')

    def isLogoMsgResponse(self, recvMsg):
        return recvMsg[5:8] == 'YAB'

    def isResponse(self, recvMsg):
        return recvMsg[0:7] == '*VK2011'

    def getCurrentTimef(self, f="%Y-%m-%d %H:%M:%S.%f"):
        return datetime.datetime.now().strftime(f)

    def getCurrentTime(self):
        return datetime.datetime.now()

    def getTimef(self, t, f="%H:%M:%S"):
        return t.strftime(f)

    def printl(self, msg, printLevel=0):
        if self.DEBUG or printLevel >= self.LOGLEVEL:
            #print("%s %s %s" % (self.getCurrentTimef(), self.imei, msg))
            print("%s %s %s" % (self.getCurrentTimef(), self.imei, msg))
            #print("%s %s" % (self.imei, msg))
    
    def shut(self, sec = 30):
        self.printl('{}秒到，我要关机了...'.format(sec))
        try:
            self.powerOff = True
            self.socket.close()
            self.timer.cancle()
            self.isStopSayHello = True
        except:
            pass

    def log(self):
        self.printl('terTotal:{:<5d} connected:{:<5d} login:{:<5d} retray:{:<5d} RECIEVE_TOTAL:{:<5d} NEED_ANSWER:{:<5d} ack:{:<5d} -> {}'.format(
            mythread.TOTAL,
            mythread.CONNECTED,
            mythread.LOGIN,
            mythread.RETRAY,
            mythread.RECIEVE_CMD_TOTAL,
            mythread.RECIEVE_CMD_NEED_ANSWER,
            mythread.ANSWER_CMD_TOTAL,
            (self.recieveTime - self.sendLoginTime).total_seconds()), 3)

    def sayHello(self):
        helloMsg = "*VK201{},AH&A1450172236915411403232860012290518&V1000000000000&B0100000000&W00&G000030&M350&N21&O1400#".format(
            self.imei)
        self.sendSocketMsg(helloMsg, printLevel=1)
        if not self.isStopSayHello:
            self.timer = threading.Timer(self.sayHelloTime, self.sayHello, ())
            self.timer.start()

    def sendSocketMsg(self, msg, printLevel=2):
        self.printl("send: {}\n".format(msg), printLevel)
        try:
            self.socket.send(msg.encode('utf-8'))
        except:
            try:
                self.socket.close()
                self.socket = ""
            except:
                pass
            self.printl("Unexpected error:{}".format(sys.exc_info()), 2)
        else:
            return True

    def recvSocketMsg(self, callback):
        while self.socket != "":
            recvData = ""
            try:
                recvData = self.socket.recv(10240)
            except:
                try:
                    if self.logined:
                        mythread.LOGIN -= 1
                        self.logined = False

                    if self.connected:
                        mythread.CONNECTED -= 1
                        self.connected = False

                    self.socket.close()
                    self.socket = ""
                except:
                    pass
                self.printl("Unexpected error:{}".format(sys.exc_info()), 2)
                self.log()
                break
            else:
                if len(recvData) != 0:
                    callback(recvData)

    def packParser(self, recvData):
        if len(recvData) == 0:
            return

        recvMsgs = recvData.decode('utf-8')
        self.printl("recvMsgs: {}".format(recvMsgs))
        msgAll = recvMsgs.split('#')
        msgList = ['{}#'.format(msg) for msg in msgAll if len(msg) != 0]

        for recvMsg in msgList:
            mythread.RECIEVE_CMD_TOTAL += 1
            # 降低心跳包日志打印级别
            self.printl("recv: {}".format(recvMsg),
                        (1 if self.isSayHello(recvMsg) else 2))

            if self.isResponse(recvMsg):

                threadLock.acquire()
                mythread.ANSWER_CMD_TOTAL += 1
                mythread.RECIEVE_CMD_NEED_ANSWER += 1
                threadLock.release()

                # 客户端应答给服务器
                recvMsgNum = recvMsg.upper().find('&T')
                responseMsg = '*VK200{},Y{}{}#'.format(
                    self.imei, recvMsg[7:9], recvMsg[recvMsgNum:-1])
                self.sendSocketMsg(responseMsg, printLevel=2)

                self.log()

            else:
                mythread.RECIEVE_CMD_NONEED_ANSWER += 1

            if self.isLogoMsgResponse(recvMsg):

                if mythread.IS_T19:
                    self.printl('t19')
                    t2 = threading.Timer(1, self.shut, ())
                    t2.start()

                if not self.logined:
                    threadLock.acquire()
                    mythread.LOGIN += 1
                    threadLock.release()

                self.logined = True
                self.isStopSayHello = False
                # 防止开启多个定时器
                if self.timer:
                    self.timer.cancel()
                self.timer = ""

                self.printl('登录成功!')
                if not self.isStopSayHello and not mythread.IS_T19:
                    self.printl('心跳 {} 秒后开始.'.format(self.sayHelloTime))
                    self.timer = threading.Timer(
                        self.sayHelloTime, self.sayHello, ())
                    self.timer.start()

                self.recieveTime = self.getCurrentTime()

                self.log()
            else:
                self.recieveTime = self.getCurrentTime()

    def run(self):
        global count, threadLock
        # threadname = threading.currentThread().getName()

        while True:
            if self.connect():
                if self.login():
                    self.recvSocketMsg(callback=self.packParser)

            self.isStopSayHello = True
            threadLock.acquire()
            if self.logined:
                self.logined = False
            mythread.RETRAY += 1
            threadLock.release()

            if not mythread.IS_T19:
                self.printl('5秒重新连接{}:{}'.format(self.server, self.port))
                time.sleep(5)
            else:
                # break
                pass
        pass


if __name__ == "__main__":
    global count, threadLock
    threads = []

    startNum = 0
    endNum = 1

    mythread.DEBUG = False
    mythread.LOGLEVEL = 2

    print(startNum)
    print(endNum)
    print(sys.argv)
    if len(sys.argv) == 2:
        startNum = int(sys.argv[1])
        endNum = int(sys.argv[1])

    if len(sys.argv) >= 3:
        startNum = int(sys.argv[1])
        endNum = int(sys.argv[2])

    if len(sys.argv) >= 5:
        mythread.DEBUG = int(sys.argv[3])
        mythread.LOGLEVEL = int(sys.argv[4])

    if len(sys.argv) >= 7:
        mythread.server = sys.argv[5]
        mythread.port = int(sys.argv[6])

    if len(sys.argv) >= 8:
        mythread.randmDurLogin = int(sys.argv[7])

    if len(sys.argv) >= 9:
        mythread.IS_T19 = (False if int(sys.argv[8]) == 0 else True)

    imeis = []
    for i in range(startNum, endNum + 1):
        imei = "58%013d" % (i)
        imeis.append(imei)

    # mythread.TOTAL = len(imeis)

    count = 1
    # create lock
    threadLock = threading.Lock()
    for imei in imeis:
        threads.append(mythread(imei, mythread.server, mythread.port))
    
    #threads.append(myPrint)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    print('程序退出')
