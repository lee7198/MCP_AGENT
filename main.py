import socketio
import threading
import time
import platform
from datetime import datetime
from qwen3_mcp import init_agent_service
from logger import Logger

CLIENT_ID = "TEST"

# 전역 로거 인스턴스 생성
logger = Logger()


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
            logger.log_event("error", f"Error sending ping: {e}")
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
    logger.log_event("error", error_msg)


@sio.event
def disconnect():
    disconnect_msg = "Disconnected from server"
    logger.log_event("system", disconnect_msg)


@sio.event
def receive_message(data):
    try:
        message = data.get("message", "")
        if not message:
            raise ValueError("Message is required")

        logger.log_event("request", message)

        sender = data.get("from")
        if not sender:
            raise ValueError("Sender is required")

        messageId = data.get("messageId")
        if not messageId:
            raise ValueError("Message ID is required")

        print("💚 ", message, messageId)

        # ARGUMENT 값만 추출
        params = [item["ARGUMENT"] for item in data["arg"]]
        logger.log_event("parameters", str(params))

        # MCP Agent 초기화
        logger.log_event("system", "MCP Agent 초기화 중...")
        bot = init_agent_service(params)
        logger.log_event("system", "MCP Agent 초기화 완료")

        # MCP 요청으로 처리
        messages = [{"role": "user", "content": message}]
        logger.log_event("system", "AI 모델 요청 시작")

        last_content = ""
        for response in bot.run(messages=messages):
            last_content = (
                response["content"] if isinstance(response, dict) else str(response)
            )

        logger.log_event("system", "AI 모델 응답 수신 완료")

        # 로그 파일로 저장
        log_filepath = logger.save_log(message, last_content, params)
        logger.log_event("system", f"요청과 응답이 저장되었습니다: {log_filepath}")

        sio.emit(
            "mcp_response",
            {
                "clientId": CLIENT_ID,
                "response": last_content,
                "to": sender,
                "messageId": messageId,
            },
        )

    except Exception as e:
        error_msg = f"Error processing received message: {e}"
        logger.log_event("error", error_msg)
        sio.emit("mcp_error", {"clientId": CLIENT_ID, "error": str(e)})


def connect_to_server():
    while True:
        try:
            logger.log_event("system", "서버에 연결을 시도합니다...")
            sio.connect("http://192.168.0.118:3001", namespaces=["/"], wait_timeout=10)
            sio.wait()
        except Exception as e:
            error_msg = f"연결 실패: {e}"
            logger.log_event("error", error_msg)
            logger.log_event("system", "5초 후 재연결을 시도합니다...")
            time.sleep(5)


if __name__ == "__main__":
    connect_to_server()
