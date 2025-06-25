# Asynchronous Web Socket Server

This server operates asynchronously and can handle 1000+ clients doing random operations simultaneously.

### Usage

* Will only work at ws://localhost:8008/ws 

- Do `python aserver.py`
- In a separate shell, do `python clients.py`
- Should expect 999 tests

There is a possibility to have `OSError: [Errno 24] Too many open files`, at which point you will need to do `ulimit -n 1024`.

### Requirements/Dependencies

- asyncio
- unittest
- json
- Python 3.7+

### Protocol

Uses HTTP POST requests to http://localhost:8008/ws to send commands in the form of JSON to the server.  The server executes and sends them back via HTTP responses with a JSON body.  Available commands are as follows:

- write (causes a lock, internally managed)
  - pass a list of keys and their values
  - must be same number of keys as values
- read
  - pass a list of keys whose values are to be read
- lock (requires a list of keys)
  - pass a list of keys and their mode (read or write)
- unlock
  - pass a list of keys

### AI used

- Copilot

### The Tricks

- Keep things small
- Use incremental development

The tutorial below got me started with quick-and-easy async Python sockets.  Copilot helped a lot with the handle_client() function.

### Non-AI Help

- https://superfastpython.com/asyncio-server/

### License

This work is licensed under GPL-3.0.
