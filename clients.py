import unittest
import asyncio
import json


class SocketClient:
    """Example client for testing the socket server."""
    
    def __init__(self, host="localhost", port=8008):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
    
    async def connect(self):
        """Connect to the server."""
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
    
    async def disconnect(self):
        """Disconnect from the server."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    async def send_command(self, command: dict) -> dict:
        if not self.writer:
            raise RuntimeError("Not connected to server")
        
        # Prepare HTTP request
        command_data = json.dumps(command).encode('utf-8')
        request = (
            "POST /ws HTTP/1.1\r\n"
            + f"Host: {self.host}\r\n"
            + "Content-Type: application/json\r\n"
            + f"Content-Length: {len(command_data)}\r\n"
            + "\r\n"
        ).encode("utf-8") + command_data

        self.writer.write(request)
        await self.writer.drain()

        # Read HTTP response headers
        response_headers = b""
        while b"\r\n\r\n" not in response_headers:
            response_headers += await self.reader.read(1)
            
        headers, _ = response_headers.split(b"\r\n\r\n", 1)
        headers = headers.decode('utf-8').split("\r\n")
        content_length = 0
        
        for header in headers:
            if header.lower().startswith("content-length:"):
                content_length = int(header.split(":")[1].strip())
                break

        # Read response body
        response_body = await self.reader.readexactly(content_length)
        print(response_body.decode('utf-8'))
        response = json.loads(response_body.decode('utf-8'))
        return response


class TestServer(unittest.IsolatedAsyncioTestCase):
    """Do 999 concurrent writes and reads to the server, plus purposeful errors."""

    async def test_mixed_clients(self):    
        import random
        number_of_clients = 333

        async def write_task(i):
            client = SocketClient()
            await client.connect()
            response = await client.send_command({
                "command": "write",
                "keys": [f"key{i}"],
                "values": [f"value{i}"],
                "hold_lock": True
            })
            await client.disconnect()
            return ("write", i, response)

        async def read_task(i):
            client = SocketClient()
            await client.connect()
            response = await client.send_command({
                "command": "read",
                "keys": [f"key{i}"],
                "values": [f"value{i}"],
                "hold_lock": False
            })
            await client.disconnect()
            return ("read", i, response)

        async def error_task(i):
            client = SocketClient()
            await client.connect()
            response = await client.send_command({
                "command": "write2",
                "keys": [f"key{i}"],
                "values": [f"value{i}"],
                "hold_lock": True
            })
            await client.disconnect()
            return ("error", i, response)

        tasks = (
            [write_task(i) for i in range(number_of_clients)] +
            [read_task(i) for i in range(number_of_clients)] +
            [error_task(i) for i in range(number_of_clients)]
        )
        random.shuffle(tasks)
        results = await asyncio.gather(*tasks)

        # You can then check results by type
        for task_type, i, result in results:
            if task_type == "write":
                self.assertTrue(result["success"])
            elif task_type == "read":
                self.assertTrue(result["success"])
                expected_key = f"key{i}"
                expected_value = f"value{i}"
                self.assertIn(expected_key, result["values"])
                self.assertEqual(result["values"][expected_key], expected_value)
            elif task_type == "error":
                self.assertFalse(result["success"])
        

if __name__ == "__main__":
    unittest.main()
