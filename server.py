#!/usr/bin/python

import socket
import select
import sys
import time
import os

# Prep work
port = int(sys.argv[1])
file = sys.argv[2]

if not os.path.isfile(file):
    print "Error: File "+file+" not found."
    sys.exit(127)
    
file = open(file, 'r', 0)
    
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.bind(("", port))
sock.listen(5)

