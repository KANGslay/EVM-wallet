#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试配置

这个模块提供测试环境的配置和辅助函数。
"""

from unittest.mock import MagicMock, patch
from web3 import Web3
from eth_account import Account
from app.models.transaction import Transaction, TransactionStatus, TransactionType

# 创建模拟的Web3提供者
def create_mock_web3():
    """
    创建一个模拟的Web3提供者，用于测试
    
    Returns:
        MagicMock: 模拟的Web3提供者
    """
    mock_w3 = MagicMock()
    
    # 模拟账户
    mock_w3.eth.accounts = [f"0x{i}" * 20 for i in range(10)]
    
    # 模拟余额存储
    balances = {}
    
    # 模拟获取余额
    def mock_get_balance(address):
        return balances.get(address, 0)
    
    mock_w3.eth.get_balance = mock_get_balance
    
    # 模拟获取nonce
    def mock_get_transaction_count(address):
        return 0  # 返回一个固定的整数值
    
    mock_w3.eth.get_transaction_count = mock_get_transaction_count
    
    # 模拟发送交易
    def mock_send_transaction(tx):
        from_address = tx.get('from')
        to_address = tx.get('to')
        value = tx.get('value', 0)
        
        # 更新余额
        if from_address in balances:
            balances[from_address] = max(0, balances.get(from_address, 0) - value)
        
        if to_address:
            balances[to_address] = balances.get(to_address, 0) + value
            
        # 返回交易哈希
        return Web3.keccak(text=f"{from_address}-{to_address}-{value}-{balances}")
    
    # 模拟发送原始交易
    def mock_send_raw_transaction(raw_tx):
        # 这里我们需要模拟交易执行过程
        # 注意: 这个行为在真实的区块链上会在矢量被打包后发生
        # 在模拟中，我们只是返回一个交易哈希
        # 创建一个唯一的交易哈希
        tx_hash = Web3.keccak(text=f"{raw_tx}")
        
        # 模拟在send_raw_transaction调用时触发代币交易执行
        # 当这个函数被调用时，它应该模拟代币转账已经执行成功
        # 注意：在真实环境中，这需要等待交易被打包
        
        # 返回交易哈希
        return tx_hash
    
    mock_w3.eth.send_raw_transaction = mock_send_raw_transaction
    
    # 模拟交易收据
    def mock_get_transaction_receipt(tx_hash):
        return {
            'status': 1,
            'blockNumber': 1,
            'gasUsed': 21000,
            'contractAddress': None
        }
    
    mock_w3.eth.get_transaction_receipt = mock_get_transaction_receipt
    
    # 模拟gas价格 - 使用整数而不是MagicMock
    mock_w3.eth.gas_price = 20000000000
    
    # 添加转换函数
    mock_w3.to_wei = Web3.to_wei
    mock_w3.from_wei = Web3.from_wei
    
    # 添加辅助函数设置余额
    def set_balance(address, amount):
        balances[address] = amount
    
    mock_w3.set_balance = set_balance
    
    return mock_w3

# 创建模拟的ERC20代币合约
def create_mock_token_contract():
    """
    创建一个模拟的ERC20代币合约，用于测试
    
    Returns:
        MagicMock: 模拟的ERC20代币合约
    """
    mock_contract = MagicMock()
    mock_contract.address = "0x" + "0" * 40  # 模拟合约地址
    
    # 创建余额存储
    balances = {}
    
    # 模拟合约函数
    mock_contract.functions.name().call.return_value = "Test Token"
    mock_contract.functions.symbol().call.return_value = "TEST"
    mock_contract.functions.decimals().call.return_value = 18
    
    # 模拟balanceOf函数
    def balance_of(address):
        mock_result = MagicMock()
        mock_result.call.return_value = balances.get(address, 0)
        return mock_result
    
    mock_contract.functions.balanceOf = balance_of
    
    # 模拟transfer函数
    def transfer(to_address, amount):
        mock_transfer = MagicMock()
        
        def transact(tx_params):
            from_address = tx_params['from']
            if balances.get(from_address, 0) < amount:
                return False
            
            balances[from_address] = balances.get(from_address, 0) - amount
            balances[to_address] = balances.get(to_address, 0) + amount
            return Web3.keccak(text=f"{from_address}-{to_address}-{amount}")
        
        # 添加build_transaction方法
        def build_transaction(tx_params):
            # 返回一个字典而不是MagicMock
            return {
                'from': tx_params.get('from', '0x0000000000000000000000000000000000000000'),
                'nonce': 0,
                'gas': 200000,
                'gasPrice': 20000000000,
                'to': to_address,
                'value': 0,
                'data': '0x',
                'chainId': 1
            }
        
        mock_transfer.transact = transact
        mock_transfer.build_transaction = build_transaction
        return mock_transfer
    
    mock_contract.functions.transfer = transfer
    
    # 模拟mint函数
    def mint(to_address, amount):
        mock_mint = MagicMock()
        
        def transact(tx_params):
            balances[to_address] = balances.get(to_address, 0) + amount
            return True
        
        mock_mint.transact = transact
        return mock_mint
    
    mock_contract.functions.mint = mint
    
    # 添加辅助函数设置余额
    def set_balance(address, amount):
        balances[address] = amount
    
    mock_contract.set_balance = set_balance
    
    return mock_contract
