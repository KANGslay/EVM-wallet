#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP服务器入口模块

用于启动 FastAPI 服务，支持 Claude Desktop / Cherry Studio 的对话请求。
"""

import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv

# 加载 .env 文件（确保环境变量正确）
load_dotenv()

# 导入 AI 路由
from app.ai.routes import router as ai_router

# 创建 FastAPI 应用
app = FastAPI(title="EVM Wallet MCP Server")

# 注册 AI 对话控制路由
app.include_router(ai_router, prefix="/ai", tags=["AI Wallet"])

# 启动服务器
if __name__ == "__main__":
    uvicorn.run("app.ai.mcp_server:app", host="0.0.0.0", port=8765, reload=True)
