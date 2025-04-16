#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
钱包服务

这个模块提供钱包服务，包括钱包的创建、查询和管理。
"""

from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.wallet import Wallet
from ..models.user import User
from ..utils.crypto import decrypt_private_key
from .blockchain import get_eth_balance, get_token_balance, get_all_balances
from ..config import settings

def create_wallet(db: Session, user: User, password: str) -> Wallet:
    """
    为用户创建钱包
    
    Args:
        db: 数据库会话
        user: 用户
        password: 用户密码，用于加密私钥
        
    Returns:
        Wallet: 创建的钱包
        
    Raises:
        HTTPException: 用户已有钱包
    """
    # 检查用户是否已有钱包
    existing_wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    if existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已有钱包"
        )
    
    # 生成新钱包
    address, encrypted_private_key, salt = Wallet.generate_wallet(password)
    
    # 创建钱包记录
    wallet = Wallet(
        address=address,
        encrypted_private_key=encrypted_private_key,
        salt=salt,
        user_id=user.id
    )
    
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    
    return wallet

def get_wallet_by_user_id(db: Session, user_id: int) -> Optional[Wallet]:
    """
    通过用户ID获取钱包
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        Optional[Wallet]: 钱包，如果用户没有钱包则返回None
    """
    return db.query(Wallet).filter(Wallet.user_id == user_id).first()