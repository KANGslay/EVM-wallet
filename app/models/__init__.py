#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库模型初始化

这个模块负责初始化SQLAlchemy和数据库连接。
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 获取数据库会话
def get_db():
    """
    获取数据库会话
    
    Yields:
        Session: 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 初始化数据库
def init_db():
    """
    初始化数据库，创建所有表
    """
    # 导入所有模型以确保它们被注册到Base中
    from . import user, wallet, transaction
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)

from .base import Base, get_db
from .user import User
from .wallet import Wallet

__all__ = ['Base', 'get_db', 'User', 'Wallet']