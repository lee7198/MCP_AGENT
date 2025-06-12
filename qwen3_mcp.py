#!/usr/bin/env python

import os
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI


def init_agent_service(arg):
    llm_cfg = {
        "model": "qwen3:8b",
        "model_server": "http://localhost:11434/v1",
        "api_key": "ollama",
        "generate_cfg": {"top_p": 0.8},
    }
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
    # Agent 초기화
    bot = Assistant(
        llm=llm_cfg,
        function_list=tools,
        name="MCP-filesystem-Bot",
        description="This bot can research local file system",
    )
    return bot


# def test(query="파일 시스템을 탐색해줘"):
#     bot = init_agent_service()
#     messages = [{"role": "user", "content": query}]
#     for response in bot.run(messages=messages):
#         print(response)


if __name__ == "__main__":
    # test("현재 디렉토리의 파일 목록을 보여줘")
    bot = init_agent_service()
    messages = [{"role": "user", "content": "hello"}]
