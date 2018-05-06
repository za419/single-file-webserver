# single-file-webserver
A Python webserver which serves a specified file as a response to any request

## Usage
Run `python server.py [portnumber] [path]` to serve the file at path on portnumber.
Requires a version2 series python.

### Caching
If you wish, you may append a `-c` flag as a third argument to specify that the server should allow the client to cache files. Note that if you do this, the browser will probably not receive new files (if you stop and restart the server with a different file) until the timeout expires.

The timeout can be specified by adding a fourth argument, including an integer number of seconds for a timeout - If you do not include this, the server will default to 3600 (one hour).
