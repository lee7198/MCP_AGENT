#!/usr/bin/env python

import os
import uuid
import json
import platform
import logging
import time
from datetime import datetime


class Logger:
    def __init__(self):
        self.events = []
        self.log_dir = "log"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # 소켓 통신 로깅 설정
        self.socket_logger = logging.getLogger("socket_client")
        self.socket_logger.setLevel(logging.INFO)
        socket_handler = logging.FileHandler(
            f'log/socket_{datetime.now().strftime("%Y%m%d")}.log'
        )
        socket_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.socket_logger.addHandler(socket_handler)

        # MCP/AI 통합 로깅 설정
        self.mcp_logger = logging.getLogger("mcp_ai")
        self.mcp_logger.setLevel(logging.INFO)
        mcp_handler = logging.FileHandler(
            f'log/mcp_ai_{datetime.now().strftime("%Y%m%d")}.log'
        )
        mcp_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.mcp_logger.addHandler(mcp_handler)

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
            self.socket_logger.info(f"{event_type}: {content}")
        # MCP/AI 관련 이벤트는 mcp_logger에 기록
        elif event_type in ["system", "error", "ai_response"]:
            self.mcp_logger.info(f"{event_type}: {content}")

    def save_log(self, message, response_text, params):
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M")
        random_hash = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{random_hash}.txt"
        filepath = os.path.join(self.log_dir, filename)

        log_data = {
            "metadata": {
                "system_info": self.get_system_info(),
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

        # AI 응답을 별도 파일로도 저장
        response_filepath = os.path.join(self.log_dir, f"response_{filename}")
        with open(response_filepath, "w", encoding="utf-8") as f:
            f.write(response_text)

        return filepath

    def get_system_info(self):
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "machine": platform.machine(),
        }
