import socket
import json 
import time
import sys
import pdb

class Slave(object):
    def __init__(self):
        pass

    def connect(self, master_ip, master_port):
        """
        Repeatedly tries to connect 
        to server until successful
        """
        try_connect = True
        while try_connect:
            try:
                self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         
                #self.soc.connect((master_ip, master_port))
                self.soc.connect((socket.gethostname(), master_port))
                try_connect = False
            except socket.error as soc_err:
                print soc_err
                self.soc.close() #if connect unsuccessful
                #Sleep for 5 seconds
                time.sleep(5)

    def hello(self):
        """
        Send initial hello 
        And wait for response
        """
        print "Sending hello"
        self.soc.send("hello")
        resp = self.soc.recv(1024)
        resp = json.loads(resp)
        print "Received response {}".format(resp)
    
    def listen(self):
        """
        Listen for new hosts 
        """
        while True:
            recv = self.soc.recv(1024)
            #When server dies, it receives empty strings
            #TODO: proper error handling when server dies
            if len(recv) > 0:
                print recv
        
    def close(self):    
        self.soc.close()

if __name__ == "__main__":
    slave = Slave()
    slave.connect("localhost", int(sys.argv[1]))
    slave.hello()
    slave.listen()
