#!/usr/bin/env python

import os
import logging
from datetime import datetime
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI

# AI 모델 로깅 설정
ai_logger = logging.getLogger("ai_model")
ai_logger.setLevel(logging.INFO)
ai_handler = logging.FileHandler(f'log/ai_{datetime.now().strftime("%Y%m%d")}.log')
ai_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
ai_logger.addHandler(ai_handler)

# MCP 서버 로깅 설정
mcp_logger = logging.getLogger("mcp_server")
mcp_logger.setLevel(logging.INFO)
mcp_handler = logging.FileHandler(f'log/mcp_{datetime.now().strftime("%Y%m%d")}.log')
mcp_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
mcp_logger.addHandler(mcp_handler)


def init_agent_service(arg):
    mcp_logger.info(f"MCP 서버 초기화 시작 - 파라미터: {arg}")
    print("😵 ARGS", arg)

    llm_cfg = {
        "model": "qwen3:8b",
        "model_server": "http://192.168.0.118:11434/v1",
        "api_key": "ollama",
        "generate_cfg": {"top_p": 0.8},
    }
    ai_logger.info(f"LLM 설정: {llm_cfg['model']} ({llm_cfg['model_server']})")

    tools = [
        {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-filesystem",
                    ]
                    + arg,
                },
            }
        }
    ]
    mcp_logger.info(f"MCP 서버 설정: {tools[0]['mcpServers']['filesystem']}")

    try:
        # Agent 초기화
        mcp_logger.info("Assistant Agent 초기화 시작")
        bot = Assistant(
            llm=llm_cfg,
            function_list=tools,
            name="MCP-filesystem-Bot",
            description="This bot can research local file system",
        )
        mcp_logger.info("Assistant Agent 초기화 완료")
        return bot
    except Exception as e:
        mcp_logger.error(f"Agent 초기화 중 오류 발생: {str(e)}")
        raise


if __name__ == "__main__":
    mcp_logger.info("프로그램 시작")
    print("init")
