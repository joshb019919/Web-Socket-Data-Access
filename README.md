# Asynchronous Web Socket Server

This server operates asynchronously and can handle 1000+ clients doing random operations simultaneously.

Given the expectation specifications (shown below but not included as file), I am assuming that shared read locks are not necessary given that their command JSON does not request a lock.

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

Uses websocket requests to ws://localhost:8008/ws to send commands in the form of JSON to the server.  The server executes and sends them back via websocket responses with a JSON body.  Available commands are as follows:

- write (causes a lock, internally managed)
  - pass a list of keys and their values
  - must be same number of keys as values
- read
  - pass a list of keys whose values are to be read
- lock (requires a list of keys)
  - pass a list of keys and their mode (read or write)
- unlock
  - pass a list of keys
 
### Example Requests and Responses
```JSON
(Read Request)
{
    "command": "read",
    "keys": ["key1", "key2"],
    "hold_lock": false
}
(Response)
{
    "success": true,
    "values": {
        "key1": "value1",
        "key2": "value2"
    }
}

(Write Request)
{
    "command": "write",
    "keys": ["key1"],
    "value": "new_value",
    "hold_lock": true
}
(Response)
{
    "success": true
}

(Lock Request)
{
    "command": "lock",
    "keys": ["key1", "key2"],
    "mode": "read"  // or "write"
}
(Response)
{
    "success": true
}

(Unlock Request)
{
    "command": "unlock",
    "keys": ["key1", "key2"]
}
(Response)
{
    "success": true
}

(Error Handling)
{
    "success": false,
    "error": "Error message describing the issue"
}
```

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
