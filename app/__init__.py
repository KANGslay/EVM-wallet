#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EVM托管钱包系统应用初始化

这个模块负责初始化FastAPI应用，注册路由和中间件。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
from .config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """
    创建并配置FastAPI应用
    
    Returns:
        FastAPI: 配置好的FastAPI应用实例
    """
    app = FastAPI(
        title="EVM托管钱包系统",
        description="基于Python的EVM托管钱包系统，支持ETH和ERC20代币管理，以及AI对话控制",
        version="0.1.0"
    )
    
    # CORS配置已移至main.py
    
    # 注册路由
    from .api.auth import router as auth_router
    from .api.wallet import router as wallet_router
    from .api.transaction import router as transaction_router
    
    app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
    app.include_router(wallet_router, prefix="/api/wallet", tags=["钱包"])
    app.include_router(transaction_router, prefix="/api/transaction", tags=["交易"])
    
    # 注册AI对话路由
    from .ai.routes import router as ai_router
    app.include_router(ai_router, prefix="/api/ai", tags=["AI对话"])
    
    # 挂载静态文件
    try:
        app.mount("/static", StaticFiles(directory="frontend"), name="static")
    except Exception as e:
        logger.warning(f"静态文件挂载失败: {e}")
    
    @app.get("/")
    async def root():
        return {"message": "欢迎使用EVM托管钱包系统"}
    
    return app