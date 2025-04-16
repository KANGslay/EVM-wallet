from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.models import get_db
from app.schemas.ai import AIRequest, AIResponse
from app.ai.chains import create_conversation_chain
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/chat", response_model=AIResponse)
async def get_ai_response(
    request: AIRequest, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    try:
        # 检查用户是否已登录
        if not current_user:
            return AIResponse(message="请先登录后再使用AI聊天功能。")
            
        # 创建对话链，传入数据库会话和当前用户
        conversation = create_conversation_chain(db=db, user=current_user)
        
        # 获取钱包状态
        from app.services.wallet import get_wallet_by_user_id
        from app.services.blockchain import get_eth_balance, get_all_balances
        
        wallet_status = "未登录用户"
        if current_user:
            wallet = get_wallet_by_user_id(db, current_user.id)
            if wallet:
                eth_balance = get_eth_balance(str(wallet.address))
                token_balances = get_all_balances(str(wallet.address))
                
                wallet_status = f"已登录用户: {current_user.username}\n" + \
                               f"钱包地址: {wallet.address}\n" + \
                               f"ETH余额: {eth_balance} ETH\n" + \
                               "代币余额:\n"
                
                for token, balance in token_balances.items():
                    wallet_status += f"- {token}: {balance}\n"
            else:
                wallet_status = f"已登录用户: {current_user.username}\n钱包状态: 未创建"
        
        # 使用process_wallet_action函数处理请求
        from app.ai.chains import process_wallet_action
        response = process_wallet_action(
            conversation=conversation,
            action=request.message,
            db=db,
            user=current_user
        )
        
        # 更新对话链的wallet_status
        conversation.memory.chat_memory.add_user_message(wallet_status)
        
        return AIResponse(message=response)
    except Exception as e:
        # 记录错误信息
        error_message = str(e)
        print(f"AI对话服务错误: {error_message}")
        
        # 根据错误类型返回不同的错误信息
        if "API request failed" in error_message:
            # API调用失败
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI服务暂时不可用，请稍后再试"
            )
        elif "API returned error" in error_message:
            # API返回错误
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"AI服务处理失败: {error_message}"
            )
        else:
            # 其他未知错误
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="系统内部错误，请联系管理员"
            )