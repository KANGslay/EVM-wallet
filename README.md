# EVM托管钱包系统

这是一个基于Python的EVM（以太坊虚拟机）托管钱包系统，具有以下功能：

## 基础功能

- 用户账号密码注册与登录
- 为每个新用户生成托管钱包（私钥和地址）
- 私钥加密存储在数据库中
- 钱包地址公开查询
- 用户查看自己的钱包地址和余额
- 用户发起ETH和ERC20代币转账
- 交易记录保存和查询

### 操作指南

#### 用户注册与登录
1. 访问系统首页，点击"注册"按钮
2. 填写用户名、密码和确认密码
3. 提交注册表单，系统将自动为您创建托管钱包
4. 使用注册的用户名和密码登录系统

#### 钱包管理
1. 登录后，在"我的钱包"页面可查看您的钱包地址和余额
2. 系统自动加密存储您的私钥，无需手动备份
3. 可通过"刷新余额"按钮更新最新的账户余额

#### 发起转账
1. 在"转账"页面，选择转账类型（ETH或ERC20代币）
2. 输入接收方地址和转账金额
3. 对于ERC20代币，需选择或输入代币合约地址
4. 确认转账信息并提交
5. 系统将使用您的托管私钥签名并广播交易

#### 交易记录
1. 在"交易记录"页面可查看所有历史交易
2. 可按交易类型、状态进行筛选
3. 点击交易ID可查看详细信息，包括区块确认数和交易哈希
4. 可通过区块浏览器链接查看链上交易详情

## AI对话控制功能

- 基于LangChain和LangGraph实现AI对话控制钱包
- 通过对话进行ETH和ERC20转账
- 通过对话查询余额
- 上下文记忆功能
- 引导用户补充信息

### 操作指南

#### 启动AI对话助手
1. 登录系统后，点击导航栏中的"AI助手"按钮
2. 系统将打开对话界面，显示欢迎信息
3. 您可以直接开始与AI助手对话

#### 通过对话查询余额
1. 直接询问："我的钱包余额是多少？"或"我有多少ETH？"
2. AI助手将自动查询并返回您的钱包余额
3. 对于ERC20代币，可以指定代币名称："我的USDT余额是多少？"

#### 通过对话发起转账
1. 使用自然语言表达转账意图，如："我想转0.1个ETH给0x123..."
2. 如果信息不完整，AI助手会引导您补充必要信息
3. AI会确认转账详情并请求您的确认
4. 确认后，系统将执行转账操作并提供交易结果

#### 上下文记忆使用
1. AI助手能够记住对话上下文，您可以在多轮对话中逐步完成操作
2. 例如，先询问余额，然后说"转一半给某地址"，AI能理解"一半"指的是之前查询的余额
3. 可以通过说"清除上下文"或"重新开始"来重置对话记忆

## MCP协议服务器

- 实现MCP协议服务器，支持WebSocket和SSE连接
- 在Claude Desktop或Cherry Studio中操作钱包
- 实现用户认证和安全通信

### 操作指南

#### 启动MCP服务器
1. 使用启动脚本运行整个系统：`./start_wallet.sh`
2. MCP服务器已在主程序中自动挂载到/mcp路径
3. 服务器默认在本地8081端口运行，支持以下端点：
   - WebSocket端点：`ws://localhost:8081/mcp/ws`
   - SSE端点：`http://localhost:8081/mcp/sse`

#### 配置Claude Desktop
1. 打开Claude Desktop应用程序
2. 进入设置页面，找到"MCP连接"选项
3. 添加新连接，使用WebSocket或SSE连接方式：
   - WebSocket地址：`ws://localhost:8081/mcp/ws`
   - SSE地址：`http://localhost:8081/mcp/sse?AUTH_TOKEN=您的JWT令牌`
4. 保存配置并重启Claude Desktop

#### 配置Cherry Studio
1. 使用项目根目录下的`cherry_studio_mcp_config.json`文件
2. 根据需要选择WebSocket或SSE连接方式
3. 在Cherry Studio平台上传配置文件
4. 详细说明请参考`CHERRY_STUDIO_MCP_CONFIG_GUIDE.md`

#### 通过AI助手使用钱包
1. 在Claude Desktop或Cherry Studio中，使用自然语言与AI助手交流
2. 可以询问钱包余额："查询我的ETH余额"
3. 发起转账："转0.01 ETH到0x123..."
4. 查询交易历史："显示我最近的交易记录"
5. 导入代币："导入USDC代币，合约地址是0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
6. AI助手将通过MCP协议与钱包系统交互，执行相应操作

## 项目结构

```
evm_wallet/
├── README.md                 # 项目说明文档
├── requirements.txt          # 项目依赖
├── .env.example             # 环境变量示例
├── start_wallet.sh          # 启动脚本
├── cherry_studio_mcp_config.json  # Cherry Studio MCP配置文件
├── CHERRY_STUDIO_MCP_CONFIG_GUIDE.md  # Cherry Studio配置指南
├── CLAUDE_MCP_CONFIG_GUIDE.md  # Claude Desktop配置指南
├── app/                     # 应用主目录
│   ├── __init__.py
│   ├── config.py            # 配置文件
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py          # 用户模型
│   │   ├── wallet.py        # 钱包模型
│   │   └── transaction.py   # 交易模型
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   ├── auth.py          # 认证服务
│   │   ├── wallet.py        # 钱包服务
│   │   ├── blockchain.py    # 区块链交互服务
│   │   └── transaction.py   # 交易服务
│   ├── api/                 # API接口
│   │   ├── __init__.py
│   │   ├── auth.py          # 认证API
│   │   ├── wallet.py        # 钱包API
│   │   └── transaction.py   # 交易API
│   ├── ai/                  # AI对话控制
│   │   ├── __init__.py
│   │   ├── chains.py        # LangChain链
│   │   ├── graphs.py        # LangGraph图
│   │   ├── prompts.py       # 提示模板
│   │   ├── custom_llm.py    # 自定义LLM封装
│   │   ├── mcp_server.py    # MCP服务器实现
│   │   └── tools.py         # 自定义工具
│   └── utils/               # 工具函数
│       ├── __init__.py
│       ├── crypto.py        # 加密工具
│       └── validators.py    # 验证工具
├── frontend/               # 前端目录
│   ├── index.html          # 主页
│   ├── css/                # 样式文件
│   ├── js/                 # JavaScript文件
│   └── img/                # 图片资源
├── logs/                   # 日志目录
│   ├── gunicorn.log        # Gunicorn日志
│   └── nginx.log           # Nginx日志
├── migrations/            # 数据库迁移
├── tests/                 # 测试目录
└── main.py                # 应用入口
```

## 技术栈

- **后端框架**: FastAPI
- **服务器**: Gunicorn, Nginx
- **数据库**: SQLite/PostgreSQL
- **区块链交互**: web3.py
- **AI对话**: LangChain, LangGraph
- **MCP协议**: WebSocket, SSE (Server-Sent Events)
- **前端**: HTML, CSS, JavaScript
- **安全性**: JWT认证, 数据加密

## 安装与运行

1. 克隆仓库
2. 创建conda环境: `conda create -n web3 python=3.10`
3. 激活环境: `conda activate web3`
4. 安装依赖: `pip install -r requirements.txt`
5. 配置环境变量: 复制`.env.example`为`.env`并填写必要配置
6. 初始化数据库: `python -m app.models.init_db`
7. 使用启动脚本运行应用: `./start_wallet.sh`

## 开发计划

1. 实现基础钱包功能
   - 用户注册登录
   - 钱包生成与管理
   - ETH和ERC20转账
   - 交易记录

2. 实现AI对话控制
   - 集成LangChain和LangGraph
   - 实现对话控制钱包功能
   - 上下文记忆与信息补充

3. 实现MCP协议服务器
   - 开发MCP服务器
   - 集成钱包功能
   - Claude Desktop集成