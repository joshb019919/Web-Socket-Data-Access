from asyncio import Lock as LockAsync
from asyncio import run as run_async
from asyncio import start_server as start_async_server
import json
import collections


class Async_Server:
    """Key-value storage server with asynchronous handling of client requests."""
    
    def __init__(self):
        self.data: dict[str, str] = {}
        self.locked_keys: list = []
        self.client_locks: dict[str, list[str]] = {}
        self.lock: LockAsync = LockAsync()

    async def write_data(self, client_id: str, keys: list[str], values: list[str]) -> bool:
        """Set list of key-value pairs for server's data storage."""
        unlocked_keys: list[str] = [key for key in keys if not any(k == key for (k, m) in self.locked_keys)]
        async with self.lock:
            self.client_locks[client_id] = keys
            for key, value in zip(keys, values):
                if key in unlocked_keys:
                    self.data[key] = value
        return True
        
    async def read_data(self, keys: list[str]) -> dict[str, str]:
        """Return dictionary of key-value pairs from server's data storage if key not locked."""
        unlocked_keys: list[str] = [key for key in keys if not any(k == key for (k, m) in self.locked_keys)]
        values: list[str|None] = [self.data.get(key, None) for key in unlocked_keys if key in self.data]
        return {k: v for k, v in zip(keys, values) if v is not None}
    
    async def lock_data(self, keys: list[str], mode: str) -> None:
        """Lock the data for the given keys for the specified mode."""
        self.locked_keys.extend((key, mode) for key in keys if (key, mode) not in self.locked_keys)
        
    async def unlock_data(self, keys: list[str]) -> None:
        """Unlock the data for the specified keys."""
        self.locked_keys = [(k, m) for (k, m) in self.locked_keys if k not in [key for key in keys]]
        
    async def handle_ws(self, websocket, path):
        addr = websocket.remote_address
        client_id = str(addr)
        
        try:
            async for message in websocket:
                try:
                    json_data = json.loads(message)
                    command = json_data.get("command")
                    
                    if command == "write":
                        success = await self.write_data(client_id, json_data.get("keys"), json_data.get("values"))
                        response = {"success": success} if success else {"success": False, "error": "Must provide equal number of keys and values"}
                    
                    elif command == "read":
                        response = await self.read_data(json_data.get("keys", []))
                        response = {"success": True, "values": response} if response else {"success": False, "error": "No data found for provided keys"}
                        
                    elif command == "lock":
                        await self.lock_data(json_data.get("keys", []), json_data.get("mode", "read"))
                        response = {"success": True}
                        
                    elif command == "unlock":
                        await self.unlock_data(json_data.get("keys", []))
                        response = {"success": True}
                        
                    else:
                        response = {"success": False, "error": "Unknown command"}
                        
                except Exception as e:
                    response = {"success": False, "error": str(e)}
                    
                await websocket.send(json.dumps(response))
                
        finally:
            # Cleanup on disconnect
            if client_id in self.client_locks:
                await self.unlock_data(self.client_locks[client_id])
                del self.client_locks[client_id]

    # async def handle_client(self, reader, writer):
    #     """Client handler for processing incoming requests."""
    #     addr = writer.get_extra_info('peername')
    #     client_id = str(addr)
        
    #     buffer = b""
    #     headers_ended = False

    #     while True:
    #         data = await reader.read(1024)
    #         if not data:
    #             break
    #         buffer += data
            
    #         if not headers_ended:
    #             header_end = buffer.find(b"\r\n\r\n")
    #             if header_end != -1:
    #                 headers_ended = True
                    
    #                 # Extract path from request line
    #                 header_bytes = buffer[:header_end]
    #                 headers = header_bytes.decode('utf-8').split("\r\n")
    #                 request_line = headers[0] if headers else ""
    #                 parts = request_line.split()
    #                 path = parts[1] if len(parts) > 1 else "/"
                    
    #                 if path != "/ws":
    #                     # Respond with 404 Not Found
    #                     response = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
    #                     writer.write(response.encode('utf-8'))
    #                     await writer.drain()
    #                     writer.close()
    #                     await writer.wait_closed()
    #                     return
                    
    #                 # Extract body if present
    #                 body = buffer[header_end + 4:]
    #                 message = body.decode('utf-8')
    #             else:
    #                 continue
    #         else:
    #             message = data.decode('utf-8')
                
    #         try:
    #             # Attempt to parse the message as JSON
    #             json_data = json.loads(message)
    #             command = json_data.get("command")
                
    #             if command == "write":
    #                 success = await self.write_data(client_id, json_data.get("keys"), json_data.get("values"))
    #                 json_data = {"success": success} if success else {"success": False, "error": "Must provide equal number of keys and values"}
                    
    #             elif command == "read":
    #                 response = await self.read_data(json_data.get("keys", []))
    #                 json_data = {"success": True, "values": response} if response else {"success": False, "error": "No data found for provided keys"}
                    
    #             elif command == "lock":
    #                 await self.lock_data(json_data.get("keys", []), json_data.get("mode", "read"))
    #                 json_data = {"success": True}
                    
    #             elif command == "unlock":
    #                 await self.unlock_data(json_data.get("keys", []))
    #                 json_data = {"success": True}
                    
    #             else:
    #                 json_data = {"success": False, "error": "Unknown command"}
                    
    #             # Prepare the response
    #             response_body = json.dumps(json_data)
    #             response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(response_body)}\r\n\r\n{response_body}"
                
    #         except json.JSONDecodeError:
    #             continue
            
    #         finally:
    #             # On disconnect, clean up any locks held by this client
    #             if client_id in self.client_locks:
    #                 await self.unlock_data(self.client_locks[client_id])
    #                 del self.client_locks[client_id]
                
    #         writer.write(response.encode('utf-8'))
    #         await writer.drain()
            
    #     writer.close()
    #     await writer.wait_closed()
    

async def main():
    
    import asyncio
    import uvloop
    import websockets
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        
    server_instance = Async_Server()
    async def ws_handler(websocket, path="/ws"):
        await server_instance.handle_ws(websocket, path)
    async with websockets.serve(ws_handler, "localhost", 8008):
        await asyncio.Future()  # run forever
    
    # server_instance = Async_Server()
    # handle_client = server_instance.handle_ws
    # server = await start_async_server(handle_client, "0.0.0.0", 8008)
    
    # async with server:
    #     await server.serve_forever()  
    
    
run_async(main())
# Note: The server will run indefinitely until manually stopped.
# To stop the server, you can use Ctrl+C in the terminal where it's running.
# Make sure to run this script in an environment that supports asyncio.
