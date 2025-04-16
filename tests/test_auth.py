import pytest
from fastapi.testclient import TestClient
from app import models
from app.utils.crypto import get_password_hash

def test_register(client, db):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "testpass123",
            "email": "test@example.com"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

    # 验证用户已存入数据库
    user = db.query(models.User).filter(models.User.username == "testuser").first()
    assert user is not None
    assert user.email == "test@example.com"

def test_login(client, db):
    # 创建测试用户，使用唯一用户名避免冲突
    hashed_password = get_password_hash("testpass123")
    test_user = models.User(
        username="loginuser",  # 使用不同的用户名
        email="login@example.com",  # 使用不同的邮箱
        hashed_password=hashed_password
    )
    db.add(test_user)
    db.commit()

    response = client.post(
        "/api/auth/login",
        json={
            "username": "loginuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    response = client.post(
        "/api/auth/login",
        json={  # 改用 json 而不是 data
            "username": "wronguser",
            "password": "wrongpass"
        }
    )
    assert response.status_code == 401