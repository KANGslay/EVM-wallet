#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
钱包模型

这个模块定义了钱包数据模型，用于管理用户钱包。
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class Wallet(Base):
    """钱包模型"""
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(42), unique=True, index=True)
    encrypted_private_key = Column(String(200))  # 加密存储的私钥
    salt = Column(String(100))  # 存储盐值
    user_id = Column(Integer, ForeignKey("users.id"))
    # SQLiteu4e0du652fu6301intervalu51fdu6570uff0cu4f7fu7528u7b80u5355u7684u65f6u95f4u5b57u6bb5uff0cu5728u6d4bu8bd5u73afu5883u4e2du66f4u517cu5bb9
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # SQLiteu4e0du652fu6301intervalu51fdu6570uff0cu4f7fu7528u7b80u5355u7684u65f6u95f4u5b57u6bb5uff0cu5728u6d4bu8bd5u73afu5883u4e2du66f4u517cu5bb9
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="wallets")
    
    @staticmethod
    def generate_wallet(password: str):
        """生成新钱包
        
        Args:
            password: 用于加密私钥的密码
            
        Returns:
            tuple: (地址, 加密私钥, 盐值)
        """
        from eth_account import Account
        import secrets
        from app.utils.crypto import encrypt_private_key
        
        # 生成随机私钥
        private_key = secrets.token_hex(32)
        account = Account.from_key(private_key)
        address = account.address
        
        # 加密私钥
        encrypted_key, salt = encrypt_private_key(private_key, password)
        
        return address, encrypted_key, salt