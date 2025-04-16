#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangChain链

这个模块实现基于LangChain的对话控制钱包功能。
"""

import re
from typing import Dict, Any, Optional
from langchain_core.runnables import RunnableSequence
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from sqlalchemy.orm import Session
from app.ai.custom_llm import SiliconFlowLLM

from app.config import settings
from app.services.wallet import get_wallet_by_user_id, create_wallet
from app.services.blockchain import (
    get_eth_balance,
    get_all_balances,
    send_eth,
    send_token,
    import_token,
    get_transaction_history
)
from app.models.user import User

from langchain.chains.llm import LLMChain
from app.config import settings
from app.services.wallet import decrypt_private_key
from app.models.transaction import Transaction

# 定义钱包操作提示模板
WALLET_TEMPLATE = """
你是一个专业的加密货币钱包助手。请根据用户的需求提供相应的钱包服务。

当前用户状态：
{wallet_status}

历史对话：
{history}

用户请求：{input}

请根据用户的请求提供适当的回应和操作建议。如果需要执行具体的钱包操作，请明确指出。
助手回应："""

def create_conversation_chain(db: Optional[Session] = None, user: Optional[User] = None):
    """创建带有钱包功能的对话链
    
    Args:
        db: 数据库会话
        user: 当前用户对象
        
    Returns:
        LLMChain: 配置好的对话链
    """
    from langchain.chains import ConversationChain, LLMChain
    from langchain.memory import ConversationBufferMemory
    from langchain.prompts import PromptTemplate
    from app.config import settings
    
    llm = SiliconFlowLLM(
        api_key=settings.OPENAI_API_KEY,
        model_name=settings.OPENAI_MODEL,
        temperature=0.7,
        max_tokens=1024
    )
    
    # 获取用户钱包状态
    wallet_status = "未登录用户"
    if db and user:
        # 确保user.id是整数类型
        user_id = user.id if isinstance(user.id, int) else int(str(user.id))
        wallet = get_wallet_by_user_id(db, user_id)
        if wallet:
            # 获取钱包余额信息
            eth_balance = get_eth_balance(str(wallet.address))
            token_balances = get_all_balances(str(wallet.address))
            
            # 格式化钱包状态信息
            wallet_status = f"已登录用户: {user.username}\n" + \
                           f"钱包地址: {wallet.address}\n" + \
                           f"ETH余额: {eth_balance} ETH\n" + \
                           "代币余额:\n"
            
            for token, balance in token_balances.items():
                wallet_status += f"- {token}: {balance}\n"
        else:
            wallet_status = f"已登录用户: {user.username}\n钱包状态: 未创建"
    
    # 创建带有钱包上下文的提示模板
    prompt = PromptTemplate(
        input_variables=["wallet_status", "history", "input"],
        template=WALLET_TEMPLATE
    )
    
    # 创建包含所有必需输入键的记忆对象
    memory = ConversationBufferMemory(
        memory_key="history",
        input_key="input"
    )
    
    # 创建对话链 - 使用兼容的格式
    # 注意：RunnableSequence的API可能在不同版本中有所不同
    # 使用最基本的方式创建对话链
    from langchain.chains import LLMChain
    
    # 使用传统的LLMChain而不是RunnableSequence
    conversation = LLMChain(
        llm=llm,
        prompt=prompt,
        memory=memory,
        verbose=True
    )
    conversation.memory = memory
    conversation.verbose = True
    
    # 重要：在API调用时手动传入wallet_status参数
    # 这样可以避免在memory中设置wallet_status
    
    return conversation

def process_wallet_action(conversation: LLMChain, action: str, db: Session, user: User) -> str:
    """处理钱包相关的操作
    
    Args:
        conversation: 对话链实例
        action: 用户请求的操作
        db: 数据库会话
        user: 当前用户对象
        
    Returns:
        str: 操作结果响应
    """
    try:
        # 检查参数
        if not db:
            print("错误: 数据库会话为空")
            return "数据库连接错误，请稍后再试。"
        if not user:
            print("错误: 用户对象为空")
            return "用户未登录，请先登录。"
        if not conversation:
            print("错误: 对话链实例为空")
            return "AI服务初始化失败，请稍后再试。"
            
        # 获取用户钱包
        # 将user.id转换为整数类型
        try:
            user_id = user.id if isinstance(user.id, int) else int(str(user.id))
            wallet = get_wallet_by_user_id(db, user_id)
        except Exception as e:
            print(f"获取钱包失败: {str(e)}")
            return f"获取钱包信息失败: {str(e)}"
        
        # 处理创建钱包请求
        if "创建钱包" in action:
            if wallet:
                return "您已经有一个钱包了，无需重复创建。"
            wallet = create_wallet(db, user, str(user.hashed_password))
            return f"钱包创建成功！您的钱包地址是: {wallet.address}"
        
        # 其他操作都需要先有钱包
        if not wallet:
            return "您还没有创建钱包，请先创建钱包。"
        
        # 初始化状态变量
        intent = "unknown"  # 默认意图
         
        # 处理查询余额请求
        if "查询余额" in action:
            eth_balance = get_eth_balance(str(wallet.address))
            token_balances = get_all_balances(str(wallet.address))
            
            response = f"ETH余额: {eth_balance} ETH\n代币余额:\n"
            for token, balance in token_balances.items():
                response += f"- {token}: {balance}\n"
            return response
        
        # 处理转账请求
        if "转账" in action or "发送" in action:
            # 解析转账信息
            try:
                # 提取转账金额和接收地址
                amount_match = re.search(r'\d+(\.\d+)?', action)
                address_match = re.search(r'0x[a-fA-F0-9]{40}', action)
                
                if not amount_match:
                    return "请提供有效的转账金额。"
                if not address_match:
                    return "请提供有效的接收地址，格式应为0x开头的42位十六进制字符。"
                
                amount = float(amount_match.group())
                to_address = address_match.group()
                
                # 获取私钥（需要实现一个安全的方式来获取私钥）
                private_key = decrypt_private_key(
                    encrypted_private_key=str(wallet.encrypted_private_key), 
                    password=str(user.hashed_password),
                    salt_str=str(wallet.salt)  # 确保salt也是字符串
                )
                
                # 判断是ETH转账还是代币转账
                if "ETH" in action.upper():
                    transaction = send_eth(
                        db=db,
                        wallet=wallet,
                        private_key=private_key,
                        to_address=to_address,
                        amount=amount
                    )
                    tx_hash = transaction.tx_hash
                else:
                    # 提取代币符号
                    token_match = re.search(r'([A-Z]{2,10})', action.upper())
                    if not token_match:
                        return "请指定要转账的代币类型。"
                    token_symbol = token_match.group(1)
                    
                    # 获取代币信息
                    if token_symbol not in settings.ERC20_TOKENS:
                        return f"未找到代币 {token_symbol} 的信息，请先导入代币。"
                    
                    token_info = settings.ERC20_TOKENS[token_symbol]
                    
                    transaction = send_token(
                        db=db,
                        wallet=wallet,
                        private_key=private_key,
                        to_address=to_address,
                        token_address=token_info['address'],
                        token_symbol=token_symbol,
                        decimals=token_info['decimals'],
                        amount=amount
                    )
                    tx_hash = transaction.tx_hash
                
                return f"转账交易已提交，交易哈希: {tx_hash}"
            except ValueError:
                return "转账信息格式不正确，请检查金额和地址格式。"
        
        # 处理导入代币请求
        if "导入代币" in action:
            try:
                # 查找合约地址
                contract_address_match = re.search(r'0x[a-fA-F0-9]{40}', action)
                if not contract_address_match:
                    return "请提供有效的代币合约地址，格式应为0x开头的42位十六进制字符。"
                
                contract_address = contract_address_match.group()
                token_info = import_token(str(wallet.address), contract_address)
                return f"代币导入成功！\n代币名称: {token_info['name']}\n代币符号: {token_info['symbol']}\n精度: {token_info['decimals']}"
            except ValueError:
                return "代币合约地址格式不正确，请检查地址格式。"
        
        # 处理交易历史请求
        if "交易历史" in action:
            # 修改函数调用，添加必要的参数
            transactions, total = get_transaction_history(
                db=db,
                address=str(wallet.address),
                page=1,  # 默认第一页
                page_size=5  # 只显示5条记录
            )
            
            if not transactions:
                return "暂无交易记录。"
            
            response = f"最近的交易记录（共{total}条）：\n"
            for tx in transactions:  # 直接使用返回的交易列表
                response += f"- 类型: {tx.type}\n  金额: {tx.amount}\n  状态: {tx.status}\n  时间: {tx.created_at}\n\n"
            
            if total > 5:
                response += "查看更多交易记录请访问交易历史页面。"
                
            return response
        
        # 如果没有匹配到具体操作，使用对话模型生成回复
        # 获取最新的钱包状态
        wallet_status = "未登录用户"
        if user:
            wallet = get_wallet_by_user_id(db, user.id)
            if wallet:
                eth_balance = get_eth_balance(str(wallet.address))
                token_balances = get_all_balances(str(wallet.address))
                
                wallet_status = f"已登录用户: {user.username}\n" + \
                               f"钱包地址: {wallet.address}\n" + \
                               f"ETH余额: {eth_balance} ETH\n" + \
                               "代币余额:\n"
                
                for token, balance in token_balances.items():
                    wallet_status += f"- {token}: {balance}\n"
            else:
                wallet_status = f"已登录用户: {user.username}\n钱包状态: 未创建"
        
        # 使用对话模型生成回复
        try:
            response = conversation.predict(input=action, wallet_status=wallet_status)
            return response
        except Exception as e:
            print(f"对话模型调用失败: {str(e)}")
            return "抱歉，AI助手暂时无法回应，请稍后再试。"
        
    except Exception as e:
        return f"操作执行失败: {str(e)}"