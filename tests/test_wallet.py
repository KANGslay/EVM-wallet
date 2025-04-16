import pytest
from eth_account import Account
from app import models

def test_create_wallet(client, db):
    # 创建测试用户并获取token
    response = client.post(
        "/api/auth/register",
        json={
            "username": "walletuser",
            "password": "testpass123",
            "email": "wallet@example.com"
        }
    )
    assert response.status_code == 201
    
    # 登录获取token
    response = client.post(
        "/api/auth/login",
        json={
            "username": "walletuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # 创建钱包
    response = client.post(
        "/api/wallet/create",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "address" in data
    assert data["address"].startswith("0x")
    
    # 验证钱包已存入数据库
    wallet = db.query(models.Wallet).filter(
        models.Wallet.address == data["address"]
    ).first()
    assert wallet is not None

def test_get_wallet_balance(client, web3_provider):
    # 创建新账户并获取地址
    account = Account.create()
    address = account.address
    
    # 使用测试网络发送一些ETH到测试地址
    test_amount = web3_provider.to_wei(1, "ether")
    
    # 获取余额
    response = client.get(f"/api/wallet/balance/{address}")
    assert response.status_code == 200
    data = response.json()
    assert "ETH" in data
    assert "balance" in data
    assert float(data["balance"]) == 1.0  # 1 ETH

def test_get_wallet_transactions(client, db):
    # 创建测试用户和钱包
    test_wallet = models.Wallet(
        address="0x1234567890123456789012345678901234567890",
        encrypted_private_key="encrypted_key_here",  # 使用加密的私钥
        user_id=1
    )
    db.add(test_wallet)
    db.commit()
    
    response = client.get(
        f"/api/wallet/transactions/{test_wallet.address}"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)  # 应该返回交易列表