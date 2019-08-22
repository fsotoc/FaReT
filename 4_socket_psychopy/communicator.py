import socket
class Communicator(object):
    def __init__(self, server = True, host='localhost', port=55250, amount=1024, sep="|"):
        self.server = server
        self.receive_buffer = ""
        self.socket = None
        self.conn = None
        self.client_address = None
        self.host = host
        self.port = port
        self.amount = amount
        self.sep = sep
        if self.server:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.conn,self.client_address = self.socket.accept()
        else:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((self.host, self.port))
    def __del__(self):
        self.conn.shutdown(1)
        if self.server:
            self.socket.close()
        self.conn.close()
    
    def close(self):
        self.conn.shutdown(1)
        if self.server:
            self.socket.close()
        self.conn.close()
        
    def send(self,  *messages):
        message = ""
        for m in messages:
            message += str(m)+self.sep
        print("Sending Message", message)
        self.conn.sendall(message)

    def receive(self):
        buffer = ""
        #try:
        r = self.conn.recv(self.amount)
        buffer += r
        while self.sep not in buffer:
            r = self.conn.recv(self.amount)
            buffer += r
        return buffer
        #except:
        #    return buffer

    def get_message(self, n=1):
        count = 0
        messages = None
        if n>1:
            messages = tuple()
    
        while count < n:
            while not self.sep in self.receive_buffer:
                self.receive_buffer += self.receive()
            i = self.receive_buffer.index(self.sep)
            message = self.receive_buffer[:i]
            self.receive_buffer = self.receive_buffer[i+1:]
            if n == 1:
                return message
            messages += (message,)
            count += 1
        return messages
    