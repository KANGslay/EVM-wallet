#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
钱包API

这个模块提供钱包API，包括钱包的创建、查询和管理。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.models import get_db
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.schemas.wallet import WalletCreate, WalletResponse
from app.services.blockchain import get_eth_balance, get_web3_provider, get_transactions
from app.services.wallet import create_wallet as create_wallet_service, get_wallet_by_user_id
from app.services.auth import get_current_user

router = APIRouter()

@router.get("/info", response_model=WalletResponse)
def get_wallet_info(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    获取当前用户的钱包信息
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        WalletResponse: 钱包信息
    """
    try:
        wallet = get_wallet_by_user_id(db, current_user.id)
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="钱包不存在，请先创建钱包"
            )
        return wallet
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取钱包信息失败: {str(e)}"
        )

@router.post("/create", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def create_wallet(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        # 创建钱包逻辑
        wallet = create_wallet_service(db, current_user, "password")
        return wallet
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/balance/{address}", response_model=Dict[str, Any])
def get_wallet_balance(address: str):
    try:
        # 获取ETH余额
        balance = get_eth_balance(address)
        return {"ETH": "ETH", "balance": balance}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/transactions/{address}", response_model=List[Dict[str, Any]])
def get_wallet_transactions(address: str, db: Session = Depends(get_db)):
    try:
        # 获取交易历史
        transactions = db.query(Transaction).filter(
            (Transaction.from_address == address) | (Transaction.to_address == address)
        ).all()
        
        # 如果数据库中没有交易记录，尝试从区块链获取
        if not transactions:
            transactions = get_transactions(address)
        
        # 转换为字典列表
        result = []
        for tx in transactions:
            if hasattr(tx, "__dict__"):
                # 数据库模型对象
                tx_dict = {k: v for k, v in tx.__dict__.items() if not k.startswith('_')}
                result.append(tx_dict)
            else:
                # 已经是字典
                result.append(tx)
                
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/send", response_model=Dict[str, Any])
def send_transaction(
    transaction_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    发送交易（ETH或ERC20代币）
    
    Args:
        transaction_data: 交易数据，包含from_address, to_address, amount, token_symbol
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        Dict[str, Any]: 交易结果
    """
    try:
        # 获取用户钱包
        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="钱包不存在，请先创建钱包"
            )
        
        # 验证发送地址是否属于当前用户
        if wallet.address.lower() != transaction_data.get("from_address", "").lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能从自己的钱包发送交易"
            )
        
        # 获取私钥（在实际应用中，应该要求用户输入密码）
        from app.utils.crypto import decrypt_private_key
        private_key = decrypt_private_key(
            encrypted_private_key=str(wallet.encrypted_private_key),
            password=str(current_user.hashed_password),  # 使用密码哈希作为密钥（不安全，仅用于演示）
            salt_str=str(wallet.salt)
        )
        
        # 根据代币类型选择不同的发送方法
        from app.services.transaction import create_eth_transaction, create_token_transaction
        
        if transaction_data.get("token_symbol", "").upper() == "ETH":
            # 发送ETH
            transaction = create_eth_transaction(
                db=db,
                user=current_user,
                wallet=wallet,
                private_key=private_key,
                to_address=transaction_data.get("to_address", ""),
                amount=float(transaction_data.get("amount", 0))
            )
        else:
            # 发送ERC20代币
            transaction = create_token_transaction(
                db=db,
                user=current_user,
                wallet=wallet,
                private_key=private_key,
                to_address=transaction_data.get("to_address", ""),
                token_symbol=transaction_data.get("token_symbol", ""),
                amount=float(transaction_data.get("amount", 0))
            )
        
        # 返回交易结果
        return {
            "tx_hash": transaction.tx_hash,
            "status": transaction.status,
            "message": "交易已提交，请等待确认"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送交易失败: {str(e)}"
        )