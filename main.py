import socketio
import uuid
import threading
import time
from qwen3_mcp import init_agent_service

CLIENT_ID = "TEST"

sio = socketio.Client(
    logger=True, engineio_logger=True, reconnection=True, reconnection_attempts=5
)


def send_ping():
    while True:
        time.sleep(180)
        try:
            data = {"clientId": CLIENT_ID}
            sio.emit("client_ping", data)
        except Exception as e:
            print(f"Error sending ping: {e}")
            break


@sio.event
def connect():
    sio.emit(
        "client_init",
        {
            "clientId": CLIENT_ID,
        },
    )

    threading.Thread(target=send_ping, daemon=True).start()


@sio.event
def force_ping():
    data = {"clientId": CLIENT_ID}
    sio.emit("client_ping", data)


@sio.event
def connect_error(data):
    print(f"Connection error: {data}")


@sio.event
def disconnect():
    print("Disconnected from server")


@sio.event
def receive_message(data):
    try:
        message = data.get("message", "")
        if not message:
            raise ValueError("Message is required")

        print("요청 : ", message)

        # ARGUMENT 값만 추출
        params = [item["ARGUMENT"] for item in data["arg"]]

        # MCP Agent 초기화
        bot = init_agent_service(params)
        # MCP 요청으로 처리
        messages = [{"role": "user", "content": message}]
        response_text = ""

        for response in bot.run(messages=messages):
            response_text += str(response)

        # print("응답: ", response_text)
        sio.emit("mcp_response", {"clientId": CLIENT_ID, "response": "response_text"})
        print("Sent MCP response")
    except Exception as e:
        print(f"Error processing received message: {e}")
        sio.emit("mcp_error", {"clientId": CLIENT_ID, "error": str(e)})


try:
    sio.connect("http://localhost:3001", wait_timeout=10)
    sio.wait()
except Exception as e:
    print(f"Connection failed: {e}")
