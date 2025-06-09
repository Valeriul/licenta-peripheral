import uasyncio as asyncio
import usocket as socket
import json
from module.module_manager import ModuleManager

async def handle_client(reader, writer):
    try:
        request = await reader.read(1024)
        request = request.decode()
        
        if not request:
            await writer.aclose()
            return
        
        request_line = request.split("\r\n")[0]
        method, path, _ = request_line.split()

        response_headers = ""
        response_body = ""

        # Endpoint: GET /test
        if method == "GET" and path == "/test":
            response_body = json.dumps({"message": "Hello, World!"})
            response_headers = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"

        # Endpoint: GET /modules
        elif method == "GET" and path == "/modules":
            json_data = {uuid: type(module).__name__ for uuid, module in ModuleManager.modules.items()}
            response_body = json.dumps(json_data)
            response_headers = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"

        # Endpoint: GET /module/state?uuid=<uuid>
        elif method == "GET" and path.startswith("/module/state"):
            query = path.split("?")[1] if "?" in path else ""
            params = dict(param.split("=") for param in query.split("&") if "=" in param)
            uuid = params.get("uuid")
            
            if not uuid:
                response_body = json.dumps({"error": "Missing 'uuid' parameter"})
                response_headers = "HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\n\r\n"
            else:
                response_body = json.dumps(ModuleManager.get_module_state(uuid))
                response_headers = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"

        # Endpoint: POST /module/state?uuid=<uuid>
        elif method == "POST" and path.startswith("/module/state"):
            query = path.split("?")[1] if "?" in path else ""
            params = dict(param.split("=") for param in query.split("&") if "=" in param)
            uuid = params.get("uuid")
            
            if not uuid:
                response_body = json.dumps({"error": "Missing 'uuid' parameter"})
                response_headers = "HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\n\r\n"
            else:
                body = request.split("\r\n\r\n", 1)[-1]
                try:
                    data = json.loads(body)
                    if "state" not in data:
                        response_body = json.dumps({"error": "Missing 'state' field"})
                        response_headers = "HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\n\r\n"
                    else:
                        response_body = json.dumps(ModuleManager.set_module_state(uuid, data["state"]))
                        response_headers = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
                except json.JSONDecodeError:
                    response_body = json.dumps({"error": "Invalid JSON"})
                    response_headers = "HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\n\r\n"
        else:
            response_body = json.dumps({"error": "Not Found"})
            response_headers = "HTTP/1.1 404 Not Found\r\nContent-Type: application/json\r\n\r\n"

        response = response_headers + response_body
        writer.write(response.encode())
        await writer.drain()
        await writer.aclose()
    except Exception as e:
        print(f"Server error: {e}")
        await writer.aclose()

async def start_server(ip_address, port=8080):
    print(f"HTTP server starting on {ip_address}:{port}")  # Debugging
    server = await asyncio.start_server(handle_client, ip_address, port)
    while True:
        await asyncio.sleep(1)  # Keep the loop running
