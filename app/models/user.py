#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户模型

这个模块定义了用户数据模型，用于用户注册和登录。
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 添加钱包关系
    wallets = relationship("Wallet", back_populates="user")
    
    # 添加交易关系
    transactions = relationship("Transaction", back_populates="user")