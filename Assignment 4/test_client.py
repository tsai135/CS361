#
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#

import zmq

context = zmq.Context()

#  Socket to talk to server
print("Connecting server…")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

request = input("Enter a request: ")
print(f"Sending request {request} …")
socket.send_string(request)

reply = socket.recv_string()
print(f"Received reply: {reply}")
