#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置模块

这个模块负责加载和管理应用配置。
"""

import os
import json
from pydantic_settings import BaseSettings
from pydantic import field_validator
from pydantic import Field, SecretStr
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import ConfigDict

# 加载.env文件中的环境变量
load_dotenv()

# 解析CORS_ORIGINS环境变量
def parse_cors_origins():
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8080,https://0.0.0.0:8080,null,http://localhost")
    if not cors_origins:
        return ["http://localhost:8080", "https://0.0.0.0:8080", "null", "http://localhost"]
        
    # 处理可能的格式问题，移除多余的引号和括号
    cors_origins = cors_origins.replace('"', '').replace("'", "").replace("[", "").replace("]", "")
    # 按逗号分割并去除空白
    return [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

class Settings(BaseSettings):
    """
    应用配置类
    """
    # 基本配置
    APP_NAME: str = "EVM托管钱包系统"
    DEBUG: bool = False
    SECRET_KEY: str = os.getenv("SECRET_KEY", "2d88e6d72c7d3f80e3afc1f61048f3c6961d547e0be1891c64dfc80be3036869")
    CORS_ORIGINS: list[str] = Field(
    default=["http://localhost:8080", "https://0.0.0.0:8080", "null", "http://localhost", "http://localhost:5173", "http://localhost:8081"],
    description="支持格式：JSON数组字符串或逗号分隔URL列表"
    )

    # CORS配置
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            if value.startswith("[") and value.endswith("]"):
                import json
                return json.loads(value)
            else:
                return [origin.strip() for origin in value.split(",")]
        return value
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./wallet.db"
    
    # JWT配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "3fe19f0fb7e18b0c69048091bfe134d41017279d2c96d22bb3a8e1f7cff31dd7")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 区块链配置
    BLOCKCHAIN_PROVIDER_URL: str = os.getenv(
        "BLOCKCHAIN_PROVIDER_URL", 
        "https://eth-sepolia.g.alchemy.com/v2/nlMrJWf3iKS6kbgP3R3sG_OkfgmOerCA"
    )
    CHAIN_ID: int = int(os.getenv("CHAIN_ID", "11155111"))  # Sepolia测试网络
    BLOCKCHAIN_CHAIN_ID: int = int(os.getenv("BLOCKCHAIN_CHAIN_ID", "1"))  # 默认为以太坊主网
    BLOCKCHAIN_CONTRACT_ADDRESS: str = os.getenv("BLOCKCHAIN_CONTRACT_ADDRESS", "0x0000000000000000000000000000000000000000")
    
    # ERC20代币列表
    ERC20_TOKENS: dict = {
        "USDT": {  # 泰达币 (Tether)
            "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # 主网合约地址
            "decimals": 6  # 小数位数
        },
        "DAI": {  # 去中心化稳定币
            "address": "0x6B175474E89094C44Da98b954EedeAC495271d0F", 
            "decimals": 18
        },
        "LINK": {  # Chainlink 代币
            "address": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
            "decimals": 18
        },
        "UNI": {  # Uniswap 治理代币
            "address": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
            "decimals": 18
        }
    }
    
    # AI配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY","fitovtoknorlfnfxnbjuwyhbhophipsmqguwvpjyyzgepcox")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "deepseek-ai/DeepSeek-R1")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
    
    # Cherry Studio配置
    CHERRY_STUDIO_API_KEY: str = os.getenv("CHERRY_STUDIO_API_KEY", "")
    CHERRY_STUDIO_API_URL: str = os.getenv("CHERRY_STUDIO_API_URL", "https://api.cherryai.com/v1")
    CHERRY_STUDIO_MODEL: str = os.getenv("CHERRY_STUDIO_MODEL", "cherry-llm")
    
    # 安全配置
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "sOqUnb2OlUCG-loI-iDTitE4Sn6o89xu_UdvOgD2tro=")
    
    # MCP服务器配置
    AUTH_TOKEN: str = os.getenv("AUTH_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MjA1OTA1OTgyNX0.kmTM8pZMELCjUlWn8c9M0_mHJ3EUtLg7Wer9z3nchtY")

    class Config:
        # 增加环境变量前缀确保字段识别
        env_prefix = "EVW_"  
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True

# 创建全局设置实例
settings = Settings()

# 删除第二个 Settings 类定义和 get_settings 函数