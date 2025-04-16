import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from web3 import Web3, EthereumTesterProvider
import sys
import os
from unittest.mock import patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings

# 使用SQLite内存数据库进行测试
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# 在导入app和models之前先修改数据库URL
settings.DATABASE_URL = SQLALCHEMY_DATABASE_URL

from app.main import app
from app.models.base import Base
from app.models import User, Wallet

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    # 确保每个测试都使用干净的会话
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(monkeypatch):
    # 确保应用使用测试数据库
    from app.models.base import get_db
    
    # 覆盖应用中的get_db依赖
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    # 使用测试客户端
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture(scope="session")
def web3_provider():
    provider = EthereumTesterProvider()
    w3 = Web3(provider)
    return w3