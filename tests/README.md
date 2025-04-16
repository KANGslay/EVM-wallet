# EVM钱包系统测试指南

## 环境准备

1. 安装测试依赖
```bash
pip install -r requirements.txt
```

2. 启动本地测试网络
安装并启动Ganache作为本地测试网络：
```bash
npm install -g ganache
ganache --port 7545
```

## 运行测试

在项目根目录下运行所有测试：
```bash
pytest
```

运行特定测试文件：
```bash
pytest tests/test_auth.py  # 测试认证功能
pytest tests/test_wallet.py  # 测试钱包功能
pytest tests/test_ai.py  # 测试AI对话功能
```

## 测试覆盖范围

- `test_auth.py`: 用户认证系统测试
  - 用户注册
  - 用户登录
  - 无效凭证处理

- `test_wallet.py`: 钱包功能测试
  - 创建钱包
  - 查询余额
  - 查询交易历史

- `test_ai.py`: AI对话功能测试
  - 对话链创建
  - AI响应测试
  - 上下文对话测试

## 注意事项

1. 测试使用SQLite内存数据库，无需额外数据库配置
2. 确保本地测试网络(Ganache)在运行测试前已启动
3. 测试用例使用pytest fixtures进行依赖注入和资源管理
4. 所有API测试使用FastAPI的TestClient进行模拟请求