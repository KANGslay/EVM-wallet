#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
交易服务

这个模块提供交易服务，包括交易的创建、查询和管理。
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from web3 import Web3
from web3.exceptions import TransactionNotFound

from ..models.transaction import Transaction, TransactionType, TransactionStatus
from ..models.wallet import Wallet
from ..models.user import User
from .blockchain import send_eth, send_token
from ..utils.validators import is_valid_eth_address, is_valid_amount, normalize_address
from ..config import settings

def create_eth_transaction(
    db: Session,
    user: User,
    wallet: Wallet,
    private_key: str,
    to_address: str,
    amount: float
) -> Transaction:
    """
    创建ETH转账交易
    
    Args:
        db: 数据库会话
        user: 用户
        wallet: 钱包
        private_key: 私钥
        to_address: 接收方地址
        amount: 转账金额
        
    Returns:
        Transaction: 创建的交易
        
    Raises:
        HTTPException: 参数无效或转账失败
    """
    # 验证参数
    normalized_address = normalize_address(to_address)
    if not normalized_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的接收方地址"
        )
    
    if not is_valid_amount(amount, 0.000001):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的转账金额，最小金额为0.000001 ETH"
        )
    
    # 发送ETH
    return send_eth(db, wallet, private_key, normalized_address, amount)

def create_token_transaction(
    db: Session,
    user: User,
    wallet: Wallet,
    private_key: str,
    to_address: str,
    token_symbol: str,
    amount: float
) -> Transaction:
    """
    创建ERC20代币转账交易
    
    Args:
        db: 数据库会话
        user: 用户
        wallet: 钱包
        private_key: 私钥
        to_address: 接收方地址
        token_symbol: 代币符号
        amount: 转账金额
        
    Returns:
        Transaction: 创建的交易
        
    Raises:
        HTTPException: 参数无效或转账失败
    """
    # 验证参数
    normalized_address = normalize_address(to_address)
    if not normalized_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的接收方地址"
        )
    
    if not is_valid_amount(amount, 0.000001):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的转账金额，最小金额为0.000001"
        )
    
    # 验证代币
    token_symbol = token_symbol.upper()
    if token_symbol not in settings.ERC20_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的代币: {token_symbol}"
        )
    
    token_info = settings.ERC20_TOKENS[token_symbol]
    
    # 发送代币
    return send_token(
        db,
        wallet,
        private_key,
        normalized_address,
        token_info["address"],
        token_symbol,
        token_info["decimals"],
        amount
    )

def get_user_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Transaction]:
    """
    获取用户交易记录
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        skip: 跳过记录数
        limit: 限制记录数
        
    Returns:
        List[Transaction]: 交易记录列表
    """
    return db.query(Transaction)\
        .filter(Transaction.user_id == user_id)\
        .order_by(Transaction.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()  # 添加.all()获取结果列表