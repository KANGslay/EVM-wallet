from pydantic import BaseModel

class AIRequest(BaseModel):
    """
    AI请求模型
    """
    message: str

class AIResponse(BaseModel):
    """
    AI响应模型
    """
    message: str