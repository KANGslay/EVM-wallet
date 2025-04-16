#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangGraph钱包对话图

这个模块实现基于LangGraph的钱包对话控制流程。
"""

import re
from typing import Dict, Any, List, Optional, Tuple, Union, Literal
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.wallet import Wallet
from app.services.wallet import get_wallet_by_user_id, create_wallet
from app.services.blockchain import (
    get_eth_balance,
    get_all_balances,
    send_eth,
    send_token,
    import_token
)
from app.utils.crypto import decrypt_private_key
from app.config import settings
from app.ai.custom_llm import SiliconFlowLLM

# 定义状态类型
class WalletState(BaseModel):
    """钱包对话状态"""
    # 对话历史
    messages: List[Union[HumanMessage, AIMessage]] = Field(default_factory=list)
    # 当前意图
    intent: Optional[str] = None
    # 收集到的参数
    params: Dict[str, Any] = Field(default_factory=dict)
    # 钱包信息
    wallet_info: Dict[str, Any] = Field(default_factory=dict)
    # 用户信息
    user_info: Dict[str, Any] = Field(default_factory=dict)
    # 数据库会话
    db: Optional[Any] = None
    # 操作结果
    result: Optional[Dict[str, Any]] = None
    # 是否需要更多信息
    need_more_info: bool = False

# 意图识别提示模板
INTENT_TEMPLATE = """
你是一个专业的加密货币钱包助手。请分析用户的请求，识别出用户的意图。

可能的意图类别：
- create_wallet: 创建钱包
- check_balance: 查询余额
- transfer_eth: 转账ETH
- transfer_token: 转账代币
- import_token: 导入代币
- unknown: 无法识别的意图

用户钱包信息：
{wallet_info}

用户请求：{input}

请识别用户意图并以JSON格式返回，格式为：{"intent": "意图类别"}
"""

# 参数提取提示模板
PARAM_TEMPLATE = """
你是一个专业的加密货币钱包助手。请从用户的请求中提取操作所需的参数。

用户意图：{intent}
用户钱包信息：
{wallet_info}

对于转账ETH，需要提取：
- to_address: 接收地址
- amount: 转账金额

对于转账代币，需要提取：
- to_address: 接收地址
- amount: 转账金额
- token_symbol: 代币符号

对于导入代币，需要提取：
- token_address: 代币合约地址

用户请求：{input}

请提取参数并以JSON格式返回，例如：{"to_address": "0x...", "amount": 0.1, "token_symbol": "USDT"}
如果某些参数缺失，请将对应字段设置为null。
"""

# 响应生成提示模板
RESPONSE_TEMPLATE = """
你是一个专业的加密货币钱包助手。请根据用户的请求和操作结果生成友好的回复。

用户意图：{intent}
操作参数：{params}
操作结果：{result}
用户钱包信息：
{wallet_info}

历史对话：
{history}

请生成一个友好、专业的回复，告知用户操作结果。如果操作成功，请给予积极的反馈；如果操作失败，请解释原因并提供解决建议。
"""

# 信息请求提示模板
INFO_REQUEST_TEMPLATE = """
你是一个专业的加密货币钱包助手。用户的请求缺少一些必要的信息，请生成一个友好的回复，引导用户提供缺失的信息。

用户意图：{intent}
已有参数：{params}
缺失参数：{missing_params}
用户钱包信息：
{wallet_info}

历史对话：
{history}

请生成一个友好、专业的回复，引导用户提供缺失的信息。请确保回复简洁明了，直接询问用户所需的信息。
"""

# 创建LLM实例
def create_llm():
    """创建LLM实例"""
    return SiliconFlowLLM(
        api_key=settings.OPENAI_API_KEY,
        model_name=settings.OPENAI_MODEL,
        temperature=0.7,
        max_tokens=1024
    )

# 意图识别节点
def identify_intent(state: WalletState) -> WalletState:
    """识别用户意图"""
    if not state.messages:
        return state

    last_message = state.messages[-1]
    if not isinstance(last_message, HumanMessage):
        return state
    
    # 初始化state变量
    if not hasattr(state, 'wallet_info'):
        state.wallet_info = {}
    if not hasattr(state, 'params'):
        state.params = {}
    if not hasattr(state, 'result'):
        state.result = None
    if not hasattr(state, 'need_more_info'):
        state.need_more_info = False

    wallet_info = "未创建钱包"
    if state.wallet_info.get("address"):
        wallet_info = f"钱包地址: {state.wallet_info.get('address')}\n"
        if state.wallet_info.get("balances"):
            wallet_info += "余额信息:\n"
            for token, balance in state.wallet_info.get("balances", {}).items():
                wallet_info += f"- {token}: {balance}\n"

    # 创建意图识别提示
    prompt = PromptTemplate(
        template=INTENT_TEMPLATE,
        input_variables=["input", "wallet_info"]
    )

    llm = create_llm()
    chain = LLMChain(llm=llm, prompt=prompt)

    # 只传入模板中定义的参数
    result = chain.invoke({"input": last_message.content, "wallet_info": wallet_info})

    # 解析结果并处理intent
    try:
        import json
        # 检查result是否包含text键
        if "text" in result:
            intent_data = json.loads(result["text"])
            # 检查是否真的是 dict 类型，避免 LLM 输出非 JSON
            if not isinstance(intent_data, dict):
                raise ValueError("返回内容不是有效的 JSON 对象")
            print("[调试] LLM 返回内容：", result["text"])

            # 自动识别 key（兼容 "intent" 或 "\"intent\""）
            for k in intent_data:
                if k.replace('"', '') == "intent":
                    state.intent = intent_data[k]
                    break
            else:
                state.intent = "unknown"
        else:
            # 如果没有text键，直接使用result作为输出
            print("[调试] LLM 返回内容：", result)
            if isinstance(result, dict) and "intent" in result:
                state.intent = result["intent"]
            else:
                state.intent = "unknown"

    except Exception as e:
        print(f"解析意图失败: {e}")
        state.intent = "unknown"

    return state



# 参数提取节点
def extract_params(state: WalletState) -> WalletState:
    """提取操作参数"""
    # 获取最新的用户消息
    if not state.messages:
        return state
    
    last_message = state.messages[-1]
    if not isinstance(last_message, HumanMessage):
        return state
    
    # 准备钱包信息
    wallet_info = "未创建钱包"
    if state.wallet_info.get("address"):
        wallet_info = f"钱包地址: {state.wallet_info.get('address')}\n"
        if state.wallet_info.get("balances"):
            wallet_info += "余额信息:\n"
            for token, balance in state.wallet_info.get("balances", {}).items():
                wallet_info += f"- {token}: {balance}\n"
    
    # 创建参数提取提示
    prompt = PromptTemplate(
        template=PARAM_TEMPLATE,
        input_variables=["input", "intent", "wallet_info"]
    )
    
    # 创建LLM链
    llm = create_llm()
    chain = LLMChain(llm=llm, prompt=prompt)
    
    # 执行链
    result = chain.invoke({
        "input": last_message.content, 
        "intent": state.intent,
        "wallet_info": wallet_info
    })
    
    # 解析结果
    try:
        import json
        params_data = json.loads(result["text"])
        # 合并新参数与现有参数
        for key, value in params_data.items():
            if value is not None:  # 只更新非空参数
                state.params[key] = value
    except Exception as e:
        print(f"解析参数失败: {e}")
    
    return state

# 检查参数完整性节点
def check_params_complete(state: WalletState) -> Literal["execute", "request_more_info"]:
    """检查参数是否完整"""
    missing_params = []
    
    if state.intent == "transfer_eth":
        if not state.params.get("to_address"):
            missing_params.append("to_address")
        if not state.params.get("amount"):
            missing_params.append("amount")
    
    elif state.intent == "transfer_token":
        if not state.params.get("to_address"):
            missing_params.append("to_address")
        if not state.params.get("amount"):
            missing_params.append("amount")
        if not state.params.get("token_symbol"):
            missing_params.append("token_symbol")
    
    elif state.intent == "import_token":
        if not state.params.get("token_address"):
            missing_params.append("token_address")
    
    # 如果有缺失参数，设置状态并返回请求更多信息
    if missing_params:
        state.need_more_info = True
        state.params["missing_params"] = missing_params
        return "request_more_info"
    
    return "execute"

# 请求更多信息节点
def request_more_info(state: WalletState) -> WalletState:
    """请求用户提供更多信息"""
    # 准备钱包信息
    wallet_info = "未创建钱包"
    if state.wallet_info.get("address"):
        wallet_info = f"钱包地址: {state.wallet_info.get('address')}\n"
        if state.wallet_info.get("balances"):
            wallet_info += "余额信息:\n"
            for token, balance in state.wallet_info.get("balances", {}).items():
                wallet_info += f"- {token}: {balance}\n"
    
    # 准备历史对话
    history = ""
    for msg in state.messages[-5:]:  # 只使用最近5条消息
        if isinstance(msg, HumanMessage):
            history += f"用户: {msg.content}\n"
        else:
            history += f"助手: {msg.content}\n"
    
    # 创建信息请求提示
    prompt = PromptTemplate(
        template=INFO_REQUEST_TEMPLATE,
        input_variables=["intent", "params", "missing_params", "wallet_info", "history"]
    )
    
    # 创建LLM链
    llm = create_llm()
    chain = LLMChain(llm=llm, prompt=prompt)
    
    # 执行链
    result = chain.invoke({
        "intent": state.intent,
        "params": {k: v for k, v in state.params.items() if k != "missing_params"},
        "missing_params": state.params.get("missing_params", []),
        "wallet_info": wallet_info,
        "history": history
    })
    
    # 添加AI回复到消息历史
    state.messages.append(AIMessage(content=result["text"]))
    
    return state

# 执行操作节点
def execute_operation(state: WalletState) -> WalletState:
    """执行钱包操作"""
    result = {"success": False, "message": "操作未执行"}
    
    try:
        # 获取数据库会话和用户
        db = state.db
        user_id = state.user_info.get("id")
        
        if not db or not user_id:
            result = {"success": False, "message": "会话无效，请重新登录"}
            state.result = result
            return state
        
        # 根据意图执行不同操作
        if state.intent == "create_wallet":
            # 检查是否已有钱包
            wallet = get_wallet_by_user_id(db, user_id)
            if wallet:
                result = {"success": False, "message": "您已经有一个钱包，无需重复创建"}
            else:
                # 创建钱包
                password = state.user_info.get("password_hash", "")
                # 从数据库获取完整的用户对象
                user = db.query(User).filter(User.id == state.user_info["id"]).first()
                wallet = create_wallet(db, user, password)
                result = {
                    "success": True, 
                    "message": "钱包创建成功",
                    "address": wallet.address
                }
                # 更新钱包信息
                state.wallet_info["address"] = wallet.address
        
        elif state.intent == "check_balance":
            # 检查是否有钱包
            wallet_address = state.wallet_info.get("address")
            if not wallet_address:
                result = {"success": False, "message": "您还没有创建钱包，请先创建钱包"}
            else:
                # 获取余额
                eth_balance = get_eth_balance(wallet_address)
                token_balances = get_all_balances(wallet_address)
                
                # 更新钱包信息
                balances = {"ETH": eth_balance}
                balances.update(token_balances)
                state.wallet_info["balances"] = balances
                
                result = {
                    "success": True,
                    "message": "余额查询成功",
                    "balances": balances
                }
        
        elif state.intent == "transfer_eth":
            # 检查是否有钱包
            wallet_address = state.wallet_info.get("address")
            if not wallet_address:
                result = {"success": False, "message": "您还没有创建钱包，请先创建钱包"}
            else:
                # 获取钱包
                wallet = get_wallet_by_user_id(db, user_id)
                if not wallet:
                    result = {"success": False, "message": "钱包不存在，请先创建钱包"}
                else:
                    # 获取转账参数
                    to_address = state.params.get("to_address")
                    amount = state.params.get("amount")
                    
                    # 获取私钥
                    password = state.user_info.get("password_hash", "")
                    private_key = decrypt_private_key(
                        encrypted_private_key=str(wallet.encrypted_private_key),
                        password=str(password),
                        salt_str=str(wallet.salt)
                    )
                    
                    # 执行转账
                    transaction = send_eth(
                        db=db,
                        wallet=wallet,
                        private_key=private_key,
                        to_address=str(to_address),
                        amount=float(amount) if amount is not None else 0.0
                    )
                    
                    result = {
                        "success": True,
                        "message": "ETH转账交易已提交",
                        "tx_hash": transaction.tx_hash
                    }
        
        elif state.intent == "transfer_token":
            # 检查是否有钱包
            wallet_address = state.wallet_info.get("address")
            if not wallet_address:
                result = {"success": False, "message": "您还没有创建钱包，请先创建钱包"}
            else:
                # 获取钱包
                wallet = get_wallet_by_user_id(db, user_id)
                if not wallet:
                    result = {"success": False, "message": "钱包不存在，请先创建钱包"}
                else:
                    # 获取转账参数
                    to_address = state.params.get("to_address")
                    amount = state.params.get("amount")
                    token_symbol = state.params.get("token_symbol")
                    
                    # 检查代币是否支持
                    if token_symbol not in settings.ERC20_TOKENS:
                        result = {"success": False, "message": f"不支持的代币: {token_symbol}"}
                    else:
                        # 获取代币信息
                        token_info = settings.ERC20_TOKENS[token_symbol]
                        
                        # 获取私钥
                        password = state.user_info.get("password_hash", "")
                        private_key = decrypt_private_key(
                            encrypted_private_key=str(wallet.encrypted_private_key),
                            password=str(password),
                            salt_str=str(wallet.salt)
                        )
                        
                        # 执行转账
                        transaction = send_token(
                            db=db,
                            wallet=wallet,
                            private_key=private_key,
                            to_address=str(to_address),
                            token_address=token_info["address"],
                            token_symbol=str(token_symbol),
                            decimals=token_info["decimals"],
                            amount=float(amount) if amount is not None else 0.0
                        )
                        
                        result = {
                            "success": True,
                            "message": f"{token_symbol}转账交易已提交",
                            "tx_hash": transaction.tx_hash
                        }
        
        elif state.intent == "import_token":
            # 检查是否有钱包
            wallet_address = state.wallet_info.get("address")
            if not wallet_address:
                result = {"success": False, "message": "您还没有创建钱包，请先创建钱包"}
            else:
                # 获取代币地址
                token_address = state.params.get("token_address")
                
                # 导入代币
                token_info = import_token(wallet_address, str(token_address))
                
                result = {
                    "success": True,
                    "message": "代币导入成功",
                    "token_info": token_info
                }
        
        else:  # unknown或其他意图
            result = {"success": False, "message": "无法识别您的请求，请尝试重新表述"}
    
    except Exception as e:
        result = {"success": False, "message": f"操作执行失败: {str(e)}"}
    
    # 设置操作结果
    state.result = result
    return state

# 生成响应节点
def generate_response(state: WalletState) -> WalletState:
    """生成响应消息"""
    # 准备钱包信息
    wallet_info = "未创建钱包"
    if state.wallet_info.get("address"):
        wallet_info = f"钱包地址: {state.wallet_info.get('address')}\n"
        if state.wallet_info.get("balances"):
            wallet_info += "余额信息:\n"
            for token, balance in state.wallet_info.get("balances", {}).items():
                wallet_info += f"- {token}: {balance}\n"
    
    # 准备历史对话
    history = ""
    for msg in state.messages[-5:]:  # 只使用最近5条消息
        if isinstance(msg, HumanMessage):
            history += f"用户: {msg.content}\n"
        else:
            history += f"助手: {msg.content}\n"
    
    # 创建响应生成提示
    prompt = PromptTemplate(
        template=RESPONSE_TEMPLATE,
        input_variables=["intent", "params", "result", "wallet_info", "history"]
    )
    
    # 创建LLM链
    llm = create_llm()
    chain = LLMChain(llm=llm, prompt=prompt)
    
    # 执行链
    result = chain.invoke({
        "intent": state.intent,
        "params": state.params,
        "result": state.result,
        "wallet_info": wallet_info,
        "history": history
    })
    
    # 添加AI回复到消息历史
    state.messages.append(AIMessage(content=result["text"]))
    
    return state

# 创建钱包对话图
def create_wallet_graph():
    """创建钱包对话图"""
    # 创建状态图
    workflow = StateGraph(WalletState)
    
    # 添加节点
    workflow.add_node("identify_intent", identify_intent)
    workflow.add_node("extract_params", extract_params)
    workflow.add_node("check_params", check_params_complete)
    workflow.add_node("request_more_info", request_more_info)
    workflow.add_node("execute_operation", execute_operation)
    workflow.add_node("generate_response", generate_response)
    
    # 设置边
    workflow.set_entry_point("identify_intent")
    workflow.add_edge("identify_intent", "extract_params")
    workflow.add_conditional_edges(
        "extract_params",
        check_params_complete,
        {
            "execute": "execute_operation",
            "request_more_info": "request_more_info"
        }
    )
    workflow.add_edge("request_more_info", END)
    workflow.add_edge("execute_operation", "generate_response")
    workflow.add_edge("generate_response", END)
    
    # 编译图
    return workflow.compile()

# 处理钱包对话
def process_wallet_graph(graph, message: str, db: Session, user: User) -> str:
    """处理钱包对话"""
    # 获取用户钱包
    # 替代方案：如果需要显式转换
    wallet = get_wallet_by_user_id(db, int(user.id.__int__()))
    
    # 准备初始状态
    state = WalletState(
        messages=[HumanMessage(content=message)],
        db=db,
        user_info={
            "id": user.id,
            "username": user.username,
            "password_hash": user.hashed_password
        },
        wallet_info={}
    )
    
    # 如果有钱包，添加钱包信息
    if wallet:
        state.wallet_info["address"] = wallet.address
        # 获取余额
        try:
            eth_balance = get_eth_balance(str(wallet.address))
            token_balances = get_all_balances(str(wallet.address))
            balances = {"ETH": eth_balance}
            balances.update(token_balances)
            state.wallet_info["balances"] = balances
        except Exception as e:
            print(f"获取余额失败: {e}")
    
    # 执行图
    result = graph.invoke(state)
    
    # 返回最后一条AI消息
    for msg in reversed(result.messages):
        if isinstance(msg, AIMessage):
            return str(msg.content)  # 确保转换为字符串
    
    return "抱歉，我无法处理您的请求。"