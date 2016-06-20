import socket               # Import socket module
import json
import pdb
import sys
import utils


class Master(object):
    def __init__(self, port):
        self.soc = socket.socket()
        host = socket.gethostname() # Get local machine name
        port = port                # Reserve a port for your service.
        print "Listening on port {}".format(port)
        self.soc.bind((host, port))        # Bind to the port
        
        self.slaves = [] #holds sockets
        self.ip_map = [] #holds host address to overlay address map


    def listen(self):
        self.soc.listen(5)                 # Now wait for client connection.
        while True:
           # Establish connection with client.
           # Send existing host_map
           #addr is a pair: (IP address, port) 
           conn, addr = self.soc.accept()     
           conn.send(json.dumps(self.ip_map))
           new_pair = (addr[0], utils.to_vxlan(addr[0]))
           self.broadcast_join(new_pair)
           self.slaves.append(conn)
           self.ip_map.append(new_pair) 
           print 'Got connection from', addr
           #conn.close()       

    def broadcast_join(self, new_addr):
        """
        Broadcast there was a new join
        """
        for conn in self.slaves:
            conn.send(json.dumps(new_addr))


    def close(self):
        #Iterate over slaves and close all connection
        pass

if __name__ == "__main__":
    master = Master(int(sys.argv[1]))
    master.listen()

