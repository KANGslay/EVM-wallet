#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证工具

这个模块提供验证功能，用于验证以太坊地址和交易金额等参数。
"""

from web3 import Web3
from eth_utils import is_hex_address, to_checksum_address
from typing import Optional

def is_valid_eth_address(address: str) -> bool:
    """
    验证以太坊地址是否有效
    
    Args:
        address: 以太坊地址
        
    Returns:
        bool: 地址是否有效
    """
    if not address:
        return False
    
    try:
        return is_hex_address(address)
    except Exception:
        return False

def normalize_address(address: str) -> Optional[str]:
    """
    规范化以太坊地址（转换为校验和地址）
    
    Args:
        address: 以太坊地址
        
    Returns:
        Optional[str]: 规范化后的地址，如果地址无效则返回None
    """
    if not is_valid_eth_address(address):
        return None
    
    try:
        return to_checksum_address(address)
    except Exception:
        return None

def is_valid_amount(amount: float, min_amount: float = 0) -> bool:
    """
    验证金额是否有效
    
    Args:
        amount: 金额
        min_amount: 最小金额
        
    Returns:
        bool: 金额是否有效
    """
    if not isinstance(amount, (int, float)):
        return False
    
    return amount > min_amount

def is_valid_gas_price(gas_price: float) -> bool:
    """
    验证gas价格是否有效
    
    Args:
        gas_price: gas价格（Gwei）
        
    Returns:
        bool: gas价格是否有效
    """
    if not isinstance(gas_price, (int, float)):
        return False
    
    return gas_price > 0

def is_valid_gas_limit(gas_limit: int) -> bool:
    """
    验证gas限制是否有效
    
    Args:
        gas_limit: gas限制
        
    Returns:
        bool: gas限制是否有效
    """
    if not isinstance(gas_limit, int):
        return False
    
    # 以太坊区块gas限制约为30,000,000，但大多数交易不需要这么多
    return 21000 <= gas_limit <= 10000000