#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import asyncio
import logging
from typing import Dict, Any

from app.models import get_db
from app.models.user import User
from app.services.auth import get_user_by_id
from app.ai.wallet_graph import create_wallet_graph, process_wallet_graph
from app.ai.chains import create_conversation_chain, process_wallet_action

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_stdio_adapter")

# 虚拟用户定义（用于无需登录的MCP请求）
class MockUser:
    def __init__(
        self,
        id: int = 1,
        username: str = "test_user",
        email: str = "test@example.com",
        hashed_password: str = "virtual_password_hash"
    ):
        self.id = id
        self.username = username
        self.email = email
        self.hashed_password = hashed_password  

# 工具定义
TOOLS = [
    {
        "name": "get_wallet_balance",
        "description": "查询钱包余额",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_transaction_history",
        "description": "获取交易历史",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "import_token",
        "description": "导入代币",
        "parameters": {
            "type": "object",
            "properties": {
                "token_address": {"type": "string"},
                "token_symbol": {"type": "string"}
            },
            "required": ["token_address"]
        }
    },
    {
        "name": "create_wallet",
        "description": "创建新钱包",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "send_transaction",
        "description": "发送交易",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "amount": {"type": "string"},
                "token": {"type": "string"}
            },
            "required": ["to", "amount"]
        }
    }
]

# 初始化对话图
wallet_graph = create_wallet_graph()

# 模拟用户对象
def get_demo_user(db):
    return db.query(User).filter(User.id == 1).first()

# 工具调用处理
async def handle_tool_call(req: Dict[str, Any]) -> Dict[str, Any]:
    name = req.get("name") or req.get("method")
    params = req.get("parameters", {})

    db = next(get_db())
    user = MockUser()  # 使用 MockUser 来模拟用户

    # 处理 mcp:list-tools 请求
    if name in ("mcp:list-tools", "list-tools"):
        result = TOOLS  # 直接返回工具列表
        return {
            "type": "tool-result",
            "call_id": req.get("call_id", "call-1"),
            "result": result
        }

    # 处理其他工具调用
    conversation = create_conversation_chain(db=db, user=user)
    result = process_wallet_action(conversation, action=name, db=db, user=user)
    return {
        "type": "tool-result",
        "call_id": req.get("call_id", "call-1"),
        "result": result
    }


# JSON-RPC 响应格式
def jsonrpc_response(req: Dict[str, Any], result: Any = None, error: str = None) -> Dict[str, Any]:
    if error:
        return {
            "jsonrpc": "2.0",
            "id": req.get("id", 0),
            "error": {"code": -1, "message": error}
        }
    return {
        "jsonrpc": "2.0",
        "id": req.get("id", 0),
        "result": result
    }

# 主循环
async def main():
    # 启动时发送一个初始化消息到标准错误（不会影响 stdio 协议）
    logger.info("MCP stdio 适配器已启动，等待请求...")
    
    while True:
        try:
            # 从标准输入读取一行
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                logger.info("标准输入已关闭，退出")
                break
                
            # 解析JSON请求
            try:
                req = json.loads(line)
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}, 输入: {line!r}")
                # 创建一个空的请求对象实例
                req = {"id": 0, "jsonrpc": "2.0"}
                print(json.dumps(jsonrpc_response(req, error=f"JSON解析错误: {e}")), flush=True)
                continue
                
            logger.info(f"收到请求: {req}")
            
            # 提取方法名 - 支持多种格式
            method = req.get("method") or req.get("type") or ""
            
            # 处理ping请求
            if method == "ping":
                print(json.dumps(jsonrpc_response(req, "pong")), flush=True)
                logger.info("已发送ping响应")
                continue
                
            # 处理 Windsurf 的初始化请求
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "serverInfo": {
                        "name": "EVM Wallet MCP Server",
                        "version": "1.0.0"
                    }
                }
                print(json.dumps(jsonrpc_response(req, result)), flush=True)
                logger.info("已发送初始化响应")
                continue

            # 处理工具列表请求 - 支持多种格式
            if method in ("mcp:list-tools", "list-tools", "tools/list"):
                # 确保每个工具都有 inputSchema 字段 (Windsurf 可能需要)
                tools_with_schema = []
                for tool in TOOLS:
                    tool_copy = tool.copy()
                    # 如果没有 inputSchema，则从 parameters 创建
                    if "inputSchema" not in tool_copy:
                        tool_copy["inputSchema"] = tool_copy.get("parameters", {})
                    tools_with_schema.append(tool_copy)
                
                # 返回工具列表
                print(json.dumps(jsonrpc_response(req, tools_with_schema), ensure_ascii=False), flush=True)
                logger.info(f"已发送工具列表响应，共 {len(tools_with_schema)} 个工具")
                continue
                
            # 处理初始化通知请求
            if method == "notifications/initialized":
                # 这是一个通知，不需要响应
                logger.info("收到初始化通知")
                continue

            # 处理工具调用 - 支持多种格式
            if method == "tool-call" or method == "mcp:tool-call" or req.get("call_id"):
                result = await handle_tool_call(req)
                print(json.dumps(result, ensure_ascii=False), flush=True)
                logger.info(f"已发送工具调用响应: {result.get('call_id', 'unknown')}")
                continue

            # 默认作为自然语言请求处理
            db = next(get_db())
            user = MockUser()  # 使用模拟用户
            message = req.get("message", req.get("params", {}).get("message", ""))
            response = process_wallet_graph(wallet_graph, message=message, db=db, user=user)
            print(json.dumps(jsonrpc_response(req, response), ensure_ascii=False), flush=True)
            logger.info("已发送自然语言响应")

        except Exception as e:
            logger.exception("处理异常")
            # 创建一个默认的请求对象，避免未定义错误
            default_req = {"id": 0, "jsonrpc": "2.0"}
            print(json.dumps(jsonrpc_response(default_req, error=str(e)), ensure_ascii=False), flush=True)

if __name__ == "__main__":
    asyncio.run(main())
