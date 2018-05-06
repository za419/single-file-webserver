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

# Helper functions
def waitingRequest(s, blocksize=4096):
    "Returns a string containing one complete HTTP request from s, loaded in chunks of blocksize"

    out = s.recv(blocksize)
    # Hopefully, our headers will be in the first blocksize.
    # But first, we know that if output is smaller than blocksize, we have everything that's ready for us
    if len(out)<blocksize:
        return out

    # While true, try to parse a content size out of our received data, and if we can't, fetch a block.
    contentSize = 0
    while True:
        block = s.recv(blocksize)
        out += block
        for line in block.split("\r\n"):
            if line.startswith("Content-Length: "):
                contentSize=int(line.split(": ")[1])
                break # Only use the first content-length header
    # "Worst" case scenario is that Content-Length is the last header.
    # In that case, we'll have four more bytes (CRLFCRLF), then the content bytes
    contentSize += 4
    # Load the content into out
    while contentSize>blocksize:
        out += s.recv(blocksize)
        contentSize -= blocksize
    if contentSize>0:
        out += s.recv(contentSize)

    # out should now contain all of our request
    return out

def basicHeaders(status, contentType):
    "Constructs and returns a basic set of headers for a response (Does not end the header block)"

    out =  "HTTP/1.0 "+status+"\r\n"
    out += "Date: "+time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())+"\r\n"
    out += "Server: Single file server (Python)\r\n"
    out += "Connection: close\r\n"
    out += "Content-Type: "+contentType+"\r\n"
    return out

def constructResponse(unendedHeaders, content):
    "Attaches unendedHeaders and content into one HTTP response (adding content-length in the process)"

    response =  unendedHeaders
    response += "Content-Length: "+str(len(content))+"\r\n\r\n"
    response += content
    return response

def sendResponse(status, contentType, content, sock):
    "Constructs and sends a response with the first three parameters via sock"

    sock.sendall(constructResponse(basicHeaders(status, contentType), content))

# Probably won't see much use for this... But need it at least for 400 bad request
def generateErrorPage(title, description):
    "Returns the HTML for an error page with title and description"

    content =  "<!DOCTYPE html>\n"
    content += "<html>\n"
    content += "  <head>\n"
    content += "    <title>"+title+"</title>\n"
    content += "  </head>\n"
    content += "  <body>\n"
    content += "    <h1 style='text-align: center; width:100%'>"+title+"</h1>\n"
    content += "    <p>"+description+"</p>\n"
    content += "  </body>\n"
    content += "</html>\n"
    return content

# Class to store an open connection
class Connection:
    def __init__(self, conn, isAccept=False):
        self.conn = conn
        self.isAccept = isAccept

    # For compatibility with select
    def fileno(self):
        return self.conn.fileno()

openconn = []

# Infinite loop to serve connections
while True:
    # List of sockets we're waiting to read from
    # (we do block on writes and local reads... But we don't want to wait on network reads.)
    r = []
    # Add all waiting connections
    for conn in openconn:
        r.append(Connection(conn))
    # And also the incoming connection accept socket
    r.append(Connection(sock, True))

    # Now, select sockets to read from
    readable, u1, u2 = select.select(r, [], [])

    # And process all those sockets
    for read in readable:
        # For the accept socket, accept the connection and add it to the list
        if read.isAccept:
            openconn.append(read.conn.accept()[0])
        else:
            # Fetch the HTTP request waiting on read
            request = waitingRequest(read.conn)
            # Lines of the HTTP request (needed to read the header)
            lines = request.split("\r\n")

            # The first reqline tells us what we're doing
            # If it's GET, we return the file specified via commandline
            # If it's HEAD, we return the headers we'd return for that file
            # If it's something else, return 400 Bad Request
            method = lines[0]
            if not (method.startswith("GET") or method.startswith("HEAD")):
                # This server can't do anything with these methods.
                # So just tell the browser it's an invalid request
                sendResponse("400 Bad Request",
                             "text/html",
                             generateErrorPage("400 Bad Request",
                                               "Your browser sent a request to perform an action the server doesn't recognize."),
                             read.conn)
                read.conn.close()
                openconn.remove(read.conn)
                continue
