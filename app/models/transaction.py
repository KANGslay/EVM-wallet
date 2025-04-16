#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
交易模型

这个模块定义了交易数据模型，用于记录用户的交易信息。
"""

from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from . import Base
from datetime import datetime
import enum

class TransactionType(str, enum.Enum):
    """
    交易类型枚举
    """
    ETH_TRANSFER = "eth_transfer"  # ETH转账
    TOKEN_TRANSFER = "token_transfer"  # 代币转账

class TransactionStatus(str, enum.Enum):
    """
    交易状态枚举
    """
    PENDING = "pending"  # 待处理
    CONFIRMED = "confirmed"  # 已确认
    FAILED = "failed"  # 失败

class Transaction(Base):
    """
    交易模型
    """
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    tx_hash = Column(String, unique=True, index=True)
    from_address = Column(String, index=True)
    to_address = Column(String, index=True)
    amount = Column(Float)
    gas_price = Column(Float)
    gas_limit = Column(Integer)
    gas_used = Column(Integer, nullable=True)
    nonce = Column(Integer)
    data = Column(Text, nullable=True)
    type = Column(Enum(TransactionType))
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    token_address = Column(String, nullable=True)  # 如果是代币转账，记录代币合约地址
    token_symbol = Column(String, nullable=True)  # 如果是代币转账，记录代币符号
    block_number = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)  # 如果交易失败，记录错误信息
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="transactions")
    
    def to_dict(self):
        """
        将交易转换为字典
        
        Returns:
            dict: 交易字典
        """
        return {
            "id": self.id,
            "tx_hash": self.tx_hash,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "amount": self.amount,
            "gas_price": self.gas_price,
            "gas_limit": self.gas_limit,
            "gas_used": self.gas_used,
            "nonce": self.nonce,
            "data": self.data,
            "type": self.type.value,
            "status": self.status.value,
            "token_address": self.token_address,
            "token_symbol": self.token_symbol,
            "block_number": self.block_number,
            "error": self.error,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }