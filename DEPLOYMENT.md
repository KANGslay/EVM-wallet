# EVM托管钱包系统部署指南

本文档提供了将EVM托管钱包系统部署到生产环境的详细步骤和最佳实践。

## 1. 环境准备

### 系统要求
- Python 3.8+
- MySQL 5.7+ 或 PostgreSQL 10+
- 足够的存储空间和内存
- 稳定的网络连接

### 安装依赖
```bash
# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 2. 配置设置

### 环境变量配置
1. 复制环境变量模板文件：
```bash
cp .env.production .env
```

2. 编辑`.env`文件，填写以下关键配置：
   - 生成安全的密钥：`SECRET_KEY`和`JWT_SECRET_KEY`
   - 配置数据库连接：`DATABASE_URL`
   - 配置区块链提供者：`BLOCKCHAIN_PROVIDER_URL`和`CHAIN_ID`
   - 配置AI服务：`OPENAI_API_KEY`等
   - 设置加密密钥：`ENCRYPTION_KEY`

### 区块链网络选择

#### 主网配置
如果您计划在以太坊主网上运行，请在`.env`文件中设置：
```
BLOCKCHAIN_PROVIDER_URL="https://mainnet.infura.io/v3/your-infura-key"
CHAIN_ID=1
```

#### 测试网配置
如果您计划在测试网上运行（推荐先在测试网验证），请设置：
```
BLOCKCHAIN_PROVIDER_URL="https://sepolia.infura.io/v3/your-infura-key"
CHAIN_ID=11155111
```

### ERC20代币配置
在`app/config.py`中配置您需要支持的ERC20代币：
```python
ERC20_TOKENS: dict = {
    "USDT": {
        "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # 主网合约地址
        "decimals": 6
    },
    # 添加其他代币...
}
```

## 3. 数据库设置

### 初始化数据库
```bash
# 使用Alembic创建数据库表
alembic upgrade head
```

### 数据备份策略
设置定期备份数据库的计划任务，特别是钱包和交易数据：
```bash
# 示例：每天凌晨2点备份数据库
0 2 * * * mysqldump -u username -p password evm_wallet_prod > /backup/evm_wallet_$(date +\%Y\%m\%d).sql
```

## 4. 安全措施

### 私钥保护
系统已实现私钥加密存储，但仍需注意：
- 定期更换`ENCRYPTION_KEY`
- 限制数据库访问权限
- 考虑使用硬件安全模块(HSM)进一步保护密钥

### API安全
- 启用HTTPS
- 设置合理的速率限制
- 实施IP白名单（如适用）

### 监控与告警
设置监控系统，对以下事件进行告警：
- 大额转账
- 异常登录
- 系统错误
- 资源使用率过高

## 5. 部署应用

### 使用Gunicorn和Nginx
```bash
# 安装Gunicorn
pip install gunicorn

# 启动应用
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8080
```

配置Nginx作为反向代理：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://0.0.0.0:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 静态文件配置
    location /static/ {
        alias /path/to/evm_wallet/frontend/;
    }
}
```

### 使用Docker部署（可选）
1. 创建Dockerfile：
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

2. 创建docker-compose.yml：
```yaml
version: '3'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
  
  db:
    image: mysql:5.7
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: evm_wallet_prod
      MYSQL_USER: username
      MYSQL_PASSWORD: password
    volumes:
      - db_data:/var/lib/mysql

volumes:
  db_data:
```

3. 启动服务：
```bash
docker-compose up -d
```

    
### 上述功能可在脚本中自动执行
```bash
# 运行脚本
./start_wallet.sh
```

4. 初始化数据库：
```bash
python init_db.py 
```

## 6. 前端部署

1. 完善前端代码，确保index.html和相关JS文件完整
2. 配置API端点指向生产环境
3. 优化静态资源加载

## 7. 系统测试

在生产环境部署后，执行以下测试：

1. 用户注册和登录
2. 钱包创建
3. 小额ETH和代币转账
4. AI对话功能
5. 负载测试

## 8. 维护计划

### 定期更新
- 安全补丁
- 依赖库更新
- 区块链协议变更适配

### 性能优化
- 定期检查数据库性能
- 优化查询
- 考虑缓存热点数据

## 9. 灾难恢复

1. 制定备份恢复流程
2. 测试恢复过程
3. 文档化紧急联系人和程序

## 10. 合规性

根据您的运营地区，确保系统符合相关法规：
- KYC/AML要求
- 数据保护法规
- 金融服务法规

## 故障排除

### 常见问题

1. **区块链连接失败**
   - 检查Infura API密钥是否有效
   - 确认网络连接稳定
   - 验证CHAIN_ID与BLOCKCHAIN_PROVIDER_URL匹配

2. **交易失败**
   - 检查账户余额是否足够
   - 确认gas价格设置合理
   - 查看区块链浏览器上的交易状态

3. **AI服务不可用**
   - 验证API密钥
   - 检查API调用限制
   - 确认网络连接到AI服务提供商

## 联系支持

如果您在部署过程中遇到问题，请联系系统开发团队获取支持。