import pytest
from unittest.mock import patch, MagicMock
from app.ai.chains import create_conversation_chain
from app.schemas.ai import AIRequest, AIResponse

@pytest.fixture
def mock_openai():
    with patch('openai.ChatCompletion.create') as mock:
        mock.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="测试回复"))]
        )
        yield mock

def test_create_conversation_chain():
    chain = create_conversation_chain()
    assert chain is not None
    # 验证链的基本属性
    assert hasattr(chain, 'predict')
    assert hasattr(chain, 'memory')

@pytest.mark.asyncio
async def test_get_ai_response(client, mock_openai, db):
    # 创建测试用户并获取认证令牌
    from app.utils.crypto import get_password_hash
    from app import models
    
    hashed_password = get_password_hash("testpass123")
    test_user = models.User(
        username="aiuser",
        email="ai@example.com",
        hashed_password=hashed_password
    )
    db.add(test_user)
    db.commit()
    
    # 登录获取令牌
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "aiuser",
            "password": "testpass123"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # 测试AI响应
    response = client.post(
        "/api/ai/chat",
        json={"message": "你好"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0

@pytest.mark.asyncio
async def test_get_ai_response_with_context(client, mock_openai, db):
    # 创建测试用户并获取认证令牌
    from app.utils.crypto import get_password_hash
    from app import models
    
    hashed_password = get_password_hash("testpass123")
    test_user = models.User(
        username="aiuser2",
        email="ai2@example.com",
        hashed_password=hashed_password
    )
    db.add(test_user)
    db.commit()
    
    # 登录获取令牌
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "aiuser2",
            "password": "testpass123"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # 测试带上下文的AI响应
    messages = [
        "你好",
        "我想了解更多关于以太坊的信息"
    ]
    
    for message in messages:
        response = client.post(
            "/api/ai/chat",
            json={"message": message},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert isinstance(data["message"], str)
        assert len(data["message"]) > 0