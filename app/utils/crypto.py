#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
加密工具

这个模块提供加密和解密功能，用于保护钱包私钥。
"""

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64
from ..config import settings
from passlib.context import CryptContext
from typing import Optional

def derive_key(password: str, salt: Optional[bytes] = None) -> tuple:
    """
    从密码派生密钥
    
    Args:
        password: 用户密码
        salt: 盐值，如果为None则生成新的盐值
        
    Returns:
        tuple: (密钥, 盐值)
    """
    if salt is None:
        salt = os.urandom(16)
    elif not isinstance(salt, bytes):
        raise ValueError("salt参数必须是bytes类型")
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256位密钥
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    
    key = kdf.derive(password.encode())
    return key, salt

def encrypt_private_key(private_key: str, password: str) -> tuple:
    """
    加密私钥
    
    Args:
        private_key: 明文私钥
        password: 用户密码
        
    Returns:
        tuple: (加密私钥, 盐值)
    """
    # 生成密钥和盐值
    key, salt = derive_key(password)
    
    # 生成随机IV
    iv = os.urandom(16)
    
    # 创建加密器
    cipher = Cipher(
        algorithms.AES(key),
        modes.CFB(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    
    # 加密私钥
    encrypted_data = encryptor.update(private_key.encode()) + encryptor.finalize()
    
    # 将IV和加密数据组合
    encrypted_private_key = base64.b64encode(iv + encrypted_data).decode()
    salt_str = base64.b64encode(salt).decode()
    
    return encrypted_private_key, salt_str

def decrypt_private_key(encrypted_private_key: str, password: str, salt_str: str) -> str:
    """
    解密私钥
    
    Args:
        encrypted_private_key: 加密私钥
        password: 用户密码
        salt_str: 盐值
        
    Returns:
        str: 解密后的私钥
    """
    try:
        # 解码盐值和加密数据
        salt = base64.b64decode(salt_str)
        encrypted_data = base64.b64decode(encrypted_private_key)
        
        # 提取IV和加密数据
        iv = encrypted_data[:16]
        encrypted_private_key_data = encrypted_data[16:]
        
        # 派生密钥
        key, _ = derive_key(password, salt)
        
        # 创建解密器
        cipher = Cipher(
            algorithms.AES(key),
            modes.CFB(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # 解密私钥
        decrypted_data = decryptor.update(encrypted_private_key_data) + decryptor.finalize()
        
        return decrypted_data.decode()
    except Exception as e:
        raise ValueError(f"解密私钥失败: {str(e)}")

# 创建密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    对密码进行哈希处理
    
    Args:
        password: 原始密码
        
    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 原始密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 验证结果
    """
    return pwd_context.verify(plain_password, hashed_password)