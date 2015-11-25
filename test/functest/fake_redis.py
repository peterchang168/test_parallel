from threading import Thread
import socket
import time
import logging
import exceptions
import threading
import random
import time
import os

global bgsave_inprogress_total
global bgsave_current_inprogress_count
bgsave_inprogress_total = 0
bgsave_current_inprogress_count =0

## Redis Server
class MessageProcesser(Thread):
    def __init__(self, oSocket, locker, logger, rand) :
        Thread.__init__(self)
        self._locker = locker
        self._logger = logger
        self._RecieveData = ""
        self._SleepTime = 0
        self._CallBackReceiver = None
        self._ReturnCallBack = None
        self._oSocket = oSocket    
        self._ResponseData = ""
        self._Corruption = "0"
        self._rand = rand

    def setCorruption(self, sCorruption) :
        self._Corruption = sCorruption
        
    def build_set_resp(self, response) :
        self._ResponseData = '%s\r\n' %response
        #print self._ResponseData

    def build_set_resp_with_len(self, response) :
        self._ResponseData = '$%d\r\n%s\r\n' %(len(response), response)

    def setSleepTime(self, tSec): 
        self._SleepTime = tSec ;
    
    def setReceiverCallbackObj(self, objCallBack):
        self._CallBackReceiver = objCallBack 
        
    def setReturnCallbackObj(self, objCallBack):
        self._ReturnCallBack = objCallBack

    def run(self):
        global bgsave_inprogress_total
        global bgsave_current_inprogress_count
        total = 0
        idx = 0
        data = []
        size = 0
        done = False
        try:
            stream = self._oSocket.recv(8192)
            #print stream
            if stream.find('\r\n')>=0:
                lines = stream.split('\r\n')
            for line in lines:
                if not line:
                    continue
                if line.find('*')>=0:
                    total = int(line[1:],10)
                elif line.lower().find('$')>=0:
                    size = int(line[1:],10)
                else:
                    data.append(line)
                    idx +=1
            self._locker.acquire(1)
            db = self._CallBackReceiver.getDB()
            if data[0].lower() == 'set':
                # set key & value
                key = data[1]
                value = data[2]
                db[key] = [value, int(time.time())+100]
                self.build_set_resp('+OK')
            if data[0].lower() == 'expire':
                # set expire of specified key only
                #print db
                key = data[1]
                ttl = int(data[2])
                if key.startswith('fail'):
                    self._locker.release()
                    try:
                        self._oSocket.shutdown(socket.SHUT_RDWR)
                    except:
                        self._oSocket.shutdown(2)
                    return
                if key.startswith('timeout'):
                    time.sleep(4)
                if ttl <= 0 :
                    self.build_set_resp('-ERR invalid expire time in SETEX')
                else:
                    if key in db and db[key][0] and db[key][1]> int(time.time()):
                        #print 'reply 1'
                        # the key exist and not expire
                        db[key][1] =  int(time.time())+ ttl
                        db[key] = [db[key][0], int(time.time())+ ttl]
                        # reply 1
                        self.build_set_resp(':1')
                    else :
                        #print 'reply 0'
                        # reply 0
                        self.build_set_resp(':0')

            if data[0].lower() == 'setex':
                # set key, value and expire
                key = data[1]
                if key.startswith('fail'):
                    self._locker.release()
                    try:
                        self._oSocket.shutdown(socket.SHUT_RDWR)
                    except:
                        self._oSocket.shutdown(2)
                    return
                if key.startswith('timeout'):
                    time.sleep(4)

                ttl = int(data[2])
                value = data[3]
                db[key] = [value, int(time.time())+ ttl]
                if ttl <= 0 :
                    self.build_set_resp('-ERR invalid expire time in SETEX')
                else :
                    self.build_set_resp('+OK')

            if data[0].lower() == 'get':
                # get value of specified key
                key = data[1]
                if key in db:
                    value = db[key][0]
                    ttl = db[key][1]
                else:
                    self._ResponseData = '$-1\r\n'
                try:
                    if int(time.time()) < int(ttl):
                        self.build_set_resp_with_len('%s' %value)
                        #print self._ResponseData
                    else:
                        self._ResponseData = '$-1\r\n'
                except:
                    self._ResponseData = '$-1\r\n'

            if data[0].lower() == 'flushdb':
                self._CallBackReceiver.cleanDB()
                self.build_set_resp('+OK')

            if data[0].lower() == 'bgsave':
                if bgsave_current_inprogress_count >= bgsave_inprogress_total:
                    self.build_set_resp('+Background saving started')
                else:
                    self.build_set_resp('-ERR Background save already in progress')
                bgsave_current_inprogress_count += 1
            if data[0].lower() == 'bgexceptioncount':
                bgsave_inprogress_total = int(data[1])
                bgsave_current_inprogress_count = 0
                self.build_set_resp('+OK')
            if data[0].lower() == 'lastsave':
                last_time = int(time.time())
                self.build_set_resp(':%d' %last_time)

            if data[0].lower() == 'ttl':
                # get ttl of specified key
                key = data[1]
                if key in db:
                    ttl = db[key][1]
                else :
                    ttl = -1
                self.build_set_resp_with_len('%d' %ttl) 

            if data[0].lower()== 'quit' :
                # get pid
                pid = os.getpid()
                #print pid
                self.build_set_resp_with_len('%s' %repr(pid))

            self._logger.debug("Message Thread Recieve data:\n%s" % data )
            try:
                self._CallBackReceiver.setMessageRecieveData(self._receieveQuery)
            except:
                pass
            self._locker.release()

            # Sleep 
            if( self._SleepTime > 0 and self._Corruption == "0" ) :
                self._locker.acquire(1)
                self._logger.debug("Message Thread Sleep Time:%dsec" % self._SleepTime)
                self._locker.release()
                time.sleep(self._SleepTime)
                
            # Corruption
            if( self._Corruption == "1" ) :
                self._locker.acquire(1)
                self._logger.debug("Message Thread Corruption!" )
                self._locker.release()
                try:
                    self._oSocket.shutdown(socket.SHUT_RDWR)
                except:
                    self._oSocket.shutdown(2)
                return 

            self._locker.acquire(1)
            self._logger.debug("Message Response data:\n%s" % self._ResponseData )
            self._locker.release()

            if not self._rand or random.random() > 0.5:            
                self._oSocket.send(self._ResponseData)
            else:
                for c in self._ResponseData:
                    self._oSocket.send(c)
            self._oSocket.close()
        except socket.error, inst:
            self._locker.acquire(1)
            self._logger.debug( "Message Thread occurs exception in socket connection[%s] " % inst)
            self._locker.release()
            return -1

        self._ReturnCallBack.finishThread()
           
    
## Redis Server
class RedisServer(Thread):
    def __init__(self, portNumber, maxThread=64, rand=False) :
        Thread.__init__(self)
        self._logger = logging.getLogger('server.RedisServer')
        self._portNumber = portNumber
        self._running = True
        self._receieveQuery = None 
        self._SleepTime = 0
        self._Corruption = "0"
        self._InSleeping = False
        self._ServerLocker = threading.RLock()
        self._threadPool = ThreadPool(maxThread, rand)
        self._db = {}
        # binding 
        try:
            self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._s.bind(('127.0.0.1', self._portNumber))
            self._s.listen(128)
        except Exception ,inst :
            self._logger.debug("Starting Redis Server failed %s" % inst)
            raise inst

    def getDB(self):
        return self._db

    def cleanDB(self):
        self._db = {}

    def setSleepTime(self, sTime):
        self._SleepTime = int(sTime) 

    def setCorruption(self, sFlag) :
        self._Corruption = sFlag         

    def run(self):
        data = ""
        try:
            self._ServerLocker.acquire(1)
            self._logger.debug("Starting accept request")
            self._ServerLocker.release()
            while self._running :
                c, addr = self._s.accept()
                while True:
                    procThread = self._threadPool.requestThread(self, c)
                    if procThread:
                        procThread.start()
                        break

                    self._ServerLocker.acquire(1)
                    self._logger.debug("Thread pool is full")
                    self._ServerLocker.release()

                    if not self._rand or random.random() > 0.5:
                        time.sleep(0.001)
                    else:
                        c.close()
                        break

        except KeyboardInterrupt:
            self._logger.debug( "occurs exception KeyboardInterrupt"  )                 
            pass
        except Exception ,inst :
            self._logger.debug( "occurs exception in new domain service[%s] " % inst)
            pass

    def stop(self) :
        if self._running == True :
            self._logger.debug( "Stoping Redis")
            # close all thread
            self._threadPool.waitThreadPool()
            self._running = False
            try:
                self._s.shutdown(socket.SHUT_RDWR)   
            except:
                self._s.shutdown(2)
            self._s.close()
            
            
    def IsSleeping(self):
        return self._InSleeping

    def WaittingWakeUp(self) :
        while self._InSleeping :
            time.sleep(1)
            
    # callback from Message processer thread
    def setMessageRecieveData(self, msg) :
        self._receieveQuery = msg 
    def getReceieveQuery(self) :
        return self._receieveQuery
        
    def clearReceieveQuery(self) :
        self._receieveQuery = None 

class ThreadPool:
    def __init__(self, maxThread, rand):
        self._rand = rand
        self._maxThread = maxThread
        self._activeThread = 0
        self._pool = {}

    def requestThread(self, server, oSocket):
        if self._activeThread > self._maxThread:
            return None

        self._activeThread += 1
        procThread = MessageProcesser(oSocket, server._ServerLocker, server._logger, self._rand)
        #procThread.setResponseText(server._response)
        procThread.setSleepTime(server._SleepTime)
        procThread.setCorruption(server._Corruption)
        procThread.setReceiverCallbackObj(server)
        procThread.setReturnCallbackObj(self)
        key = "%s%s" % (time.time(), procThread.getName())
        self._pool[key] = procThread
        return procThread

    def waitThreadPool(self):
        for key in self._pool:
            self._pool[key].join()

    def finishThread(self):
        self._activeThread -= 1
        #print 'active thread %d' %self._activeThread

if __name__ == '__main__':
    nds = RedisServer(6379)
    nds.start()

