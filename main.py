import socketio
import uuid
import threading
import time
import os
import json
import platform
from datetime import datetime
from qwen3_mcp import init_agent_service
from logger import Logger

CLIENT_ID = "TEST"

# 전역 로거 인스턴스 생성
logger = Logger()


def custom_print(message):
    print(message)
    logger.log_event("print", message)


def get_system_info():
    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": platform.python_version(),
        "machine": platform.machine(),
    }


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
    logger.log_event("system", "서버에 연결되었습니다.")
    threading.Thread(target=send_ping, daemon=True).start()


@sio.event
def force_ping():
    data = {"clientId": CLIENT_ID}
    sio.emit("client_ping", data)


@sio.event
def connect_error(data):
    error_msg = f"Connection error: {data}"
    custom_print(error_msg)
    logger.log_event("error", error_msg)


@sio.event
def disconnect():
    disconnect_msg = "Disconnected from server"
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

        last_content = ""
        for response in bot.run(messages=messages):
            last_content = (
                response["content"] if isinstance(response, dict) else str(response)
            )

        custom_print("AI 모델 응답 수신 완료")
        logger.log_event("ai_response", last_content)

        # 로그 파일로 저장
        log_filepath = logger.save_log(message, last_content, params)
        custom_print(f"요청과 응답이 저장되었습니다: {log_filepath}")

        sio.emit(
            "mcp_response",
            {"clientId": CLIENT_ID, "response": "😛😛😛😛😛😛😛😛😛😛😛😛😛😛😛"},
        )
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
