import unittest
import asyncio
import json
import websockets


class SocketClient:
    def __init__(self, host="localhost", port=8008, path="/ws"):
        self.uri = f"ws://{host}:{port}{path}"
        self.websocket = None

    async def connect(self):
        self.websocket = await websockets.connect(self.uri)

    async def disconnect(self):
        if self.websocket:
            await self.websocket.close()

    async def send_command(self, command: dict) -> dict:
        if not self.websocket:
            raise RuntimeError("Not connected to server")
        await self.websocket.send(json.dumps(command))
        response = await self.websocket.recv()
        return json.loads(response)


class TestServer(unittest.IsolatedAsyncioTestCase):
    """Do 999 concurrent writes and reads to the server, plus purposeful errors."""
    
    threads = []

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
