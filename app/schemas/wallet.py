from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class WalletBase(BaseModel):
    """钱包基础模型"""
    address: str = Field(..., description="钱包地址")
    name: Optional[str] = Field(None, description="钱包名称")

class WalletCreate(WalletBase):
    """钱包创建请求模型"""
    user_id: int = Field(..., description="用户ID")

class WalletResponse(WalletBase):
    """钱包响应模型"""
    id: int
    user_id: int
    balance: float = Field(0.0, description="ETH余额")
    created_at: datetime
    
    class Config:
        from_attributes = True