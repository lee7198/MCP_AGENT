#!/usr/bin/env python

from qwen_agent.agents import Assistant
from logger import Logger

# 전역 로거 인스턴스 생성
logger = Logger()


def init_agent_service(arg):
    logger.log_event("system", f"MCP 서버 초기화 시작 - 파라미터: {arg}")

    llm_cfg = {
        "model": "qwen3:8b",
        "model_server": "http://192.168.0.118:11434/v1",
        "api_key": "ollama",
        "generate_cfg": {"top_p": 0.8},
    }
    logger.log_event(
        "system", f"LLM 설정: {llm_cfg['model']} ({llm_cfg['model_server']})"
    )

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
    logger.log_event("system", f"MCP 서버 설정: {tools[0]['mcpServers']['filesystem']}")

    try:
        # Agent 초기화
        logger.log_event("system", "Assistant Agent 초기화 시작")
        bot = Assistant(
            llm=llm_cfg,
            function_list=tools,
            name="MCP-filesystem-Bot",
            description="This bot can research local file system",
        )
        logger.log_event("system", "Assistant Agent 초기화 완료")
        return bot
    except Exception as e:
        logger.log_event("error", f"Agent 초기화 중 오류 발생: {str(e)}")
        raise


if __name__ == "__main__":
    logger.log_event("system", "프로그램 시작")
