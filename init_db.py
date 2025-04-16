#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库初始化脚本

这个脚本用于初始化数据库表结构。
"""

from app.models.base import Base, engine
from app.models.user import User
from app.models.wallet import Wallet
from app.models.transaction import Transaction

# 创建所有表
print("正在创建数据库表...")
Base.metadata.create_all(bind=engine)
print("数据库表创建完成！")