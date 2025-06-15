import socketio
import uuid
import threading
import time
import os
import json
import platform
import logging
from datetime import datetime
from qwen3_mcp import init_agent_service

CLIENT_ID = "TEST"

# 소켓 통신 로깅 설정
socket_logger = logging.getLogger("socket_client")
socket_logger.setLevel(logging.INFO)
socket_handler = logging.FileHandler(
    f'log/socket_{datetime.now().strftime("%Y%m%d")}.log'
)
socket_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
socket_logger.addHandler(socket_handler)


class Logger:
    def __init__(self):
        self.events = []
        self.log_dir = "log"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def log_event(self, event_type, content):
        timestamp = datetime.now()
        self.events.append(
            {
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "type": event_type,
                "content": content,
            }
        )
        # 소켓 관련 이벤트는 socket_logger에 기록
        if event_type in ["system", "error"] and (
            "서버" in content or "연결" in content
        ):
            socket_logger.info(f"{event_type}: {content}")

    def save_log(self, message, response_text, params):
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M")
        random_hash = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{random_hash}.txt"
        filepath = os.path.join(self.log_dir, filename)

        log_data = {
            "metadata": {
                "client_id": CLIENT_ID,
                "system_info": get_system_info(),
                "timestamp": {
                    "iso": now.isoformat(),
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M:%S"),
                    "timezone": time.tzname[0],
                },
            },
            "request": {
                "message": message,
                "parameters": params,
                "received_at": now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            },
            "response": {
                "content": response_text,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            },
            "events": self.events,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

        return filepath


def get_system_info():
    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": platform.python_version(),
        "machine": platform.machine(),
    }


# 전역 로거 인스턴스 생성
logger = Logger()


def custom_print(message):
    print(message)
    logger.log_event("print", message)


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
    socket_logger.info("서버에 연결되었습니다.")
    logger.log_event("system", "서버에 연결되었습니다.")
    threading.Thread(target=send_ping, daemon=True).start()


@sio.event
def force_ping():
    data = {"clientId": CLIENT_ID}
    sio.emit("client_ping", data)


@sio.event
def connect_error(data):
    error_msg = f"Connection error: {data}"
    socket_logger.error(error_msg)
    custom_print(error_msg)
    logger.log_event("error", error_msg)


@sio.event
def disconnect():
    disconnect_msg = "Disconnected from server"
    socket_logger.info(disconnect_msg)
    custom_print(disconnect_msg)
    logger.log_event("system", disconnect_msg)


@sio.event
def receive_message(data):
    try:
        message = data.get("message", "")
        if not message:
            raise ValueError("Message is required")

        custom_print("요청 : " + message)
        logger.log_event("request", message)

        # ARGUMENT 값만 추출
        params = [item["ARGUMENT"] for item in data["arg"]]
        custom_print(f"😵 ARGS {params}")
        logger.log_event("parameters", str(params))

        # MCP Agent 초기화
        custom_print("MCP Agent 초기화 중...")
        logger.log_event("system", "MCP Agent 초기화 시작")
        bot = init_agent_service(params)
        logger.log_event("system", "MCP Agent 초기화 완료")

        # MCP 요청으로 처리
        messages = [{"role": "user", "content": message}]
        custom_print("AI 모델에 요청 전송 중...")
        logger.log_event("system", "AI 모델 요청 시작")

        response_text = ""
        for response in bot.run(messages=messages):
            response_text += str(response)
            custom_print(f"AI 모델 응답 수신: {response}")
            logger.log_event("ai_response", str(response))

        custom_print("응답: " + response_text)
        logger.log_event("response", response_text)

        # 로그 파일로 저장
        log_filepath = logger.save_log(message, response_text, params)
        custom_print(f"요청과 응답이 저장되었습니다: {log_filepath}")

        sio.emit("mcp_response", {"clientId": CLIENT_ID, "response": "response_text"})
    except Exception as e:
        error_msg = f"Error processing received message: {e}"
        custom_print(error_msg)
        logger.log_event("error", error_msg)
        sio.emit("mcp_error", {"clientId": CLIENT_ID, "error": str(e)})


def connect_to_server():
    while True:
        try:
            custom_print("서버에 연결을 시도합니다...")
            sio.connect("http://192.168.0.118:3001", wait_timeout=10)
            sio.wait()
        except Exception as e:
            error_msg = f"연결 실패: {e}"
            custom_print(error_msg)
            logger.log_event("error", error_msg)
            custom_print("5초 후 재연결을 시도합니다...")
            time.sleep(5)


if __name__ == "__main__":
    connect_to_server()
