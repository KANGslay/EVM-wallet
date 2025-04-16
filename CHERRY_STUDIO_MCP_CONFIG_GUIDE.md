# Cherry Studio MCP 配置指南

## 概述

MCP (Model Control Protocol) 是一种允许AI助手与外部系统进行通信的协议。本指南将帮助您配置Cherry Studio以通过MCP协议与EVM托管钱包系统进行交互，实现查询余额、发起转账等操作。

## 前提条件

- EVM托管钱包系统已安装并运行
- 已创建用户账户并登录系统
- Cherry Studio API密钥（在Cherry Studio平台获取）

## 配置步骤

### 1. 确保MCP服务器已启动

在配置Cherry Studio之前，请确保EVM托管钱包系统的MCP服务器已经启动：

```bash
# 启动EVM托管钱包系统
./start_wallet.sh

# MCP服务器已在主程序中自动挂载到/mcp路径
```

服务器默认在本地8081端口运行，支持两种连接方式：
- WebSocket端点：`ws://localhost:8081/mcp/ws`
- SSE (Server-Sent Events)端点：`http://localhost:8081/mcp/sse`

### 2. 获取认证令牌

您需要一个有效的JWT令牌来认证MCP连接：

1. 登录EVM托管钱包系统Web界面（http://localhost）
2. 在浏览器开发者工具中，从localStorage或应用程序请求头中复制`token`值

### 3. 配置Cherry Studio MCP连接

1. 在项目根目录下找到`cherry_studio_mcp_config.json`文件
2. 根据您选择的连接方式（WebSocket或SSE）更新配置文件

#### WebSocket配置示例

```json
{
  "mcpServers": {
    "evm_wallet_server": {
      "name": "EVM托管钱包",
      "description": "通过Cherry Studio操作EVM托管钱包系统",
      "baseUrl": "ws://localhost:8081/mcp/ws",
      "protocol": "websocket",
      "command": "",
      "args": [],
      "env": {
        "AUTH_TOKEN": "您的JWT令牌"
      },
      "isActive": true
    }
  }
}
```

#### SSE配置示例（推荐）

```json
{
  "mcpServers": {
    "evm_wallet_server": {
      "name": "EVM托管钱包",
      "description": "通过Cherry Studio操作EVM托管钱包系统",
      "baseUrl": "http://localhost:8081/mcp/sse?AUTH_TOKEN=您的JWT令牌",
      "protocol": "sse",
      "messageEndpoint": "http://localhost:8081/mcp/sse/message?AUTH_TOKEN=您的JWT令牌",
      "command": "",
      "args": [],
      "env": {
        "AUTH_TOKEN": "您的JWT令牌"
      },
      "isActive": true
    }
  }
}
```

> **注意**：使用SSE配置时，请将认证令牌直接作为URL参数添加到`baseUrl`和`messageEndpoint`中，这样可以避免认证问题。

### 4. 在Cherry Studio中配置MCP

1. 登录Cherry Studio平台
2. 创建新项目或选择现有项目
3. 在项目设置中，找到「外部集成」或「MCP配置」选项
4. 上传您修改后的`cherry_studio_mcp_config.json`文件
5. 保存配置

## 使用MCP功能

配置完成后，您可以在Cherry Studio中使用以下功能：

- **查询钱包余额**：AI助手可以查询您的ETH和代币余额
- **发送资产**：AI助手可以帮助您发送ETH或代币到指定地址
- **查看交易历史**：AI助手可以获取并展示您的交易记录
- **导入代币**：AI助手可以帮助您导入新的代币

## 示例提示词

以下是一些您可以在Cherry Studio中使用的示例提示词：

```
查询我的钱包余额
发送0.01 ETH到0x742d35Cc6634C0532925a3b844Bc454e4438f44e
导入USDC代币，合约地址是0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
查看我最近的交易记录
```

## 故障排除

如果您在使用过程中遇到问题：

1. **认证错误（401）**：
   - 确保JWT令牌有效且未过期
   - 对于SSE连接，确保令牌已作为URL参数添加到`baseUrl`和`messageEndpoint`中
   - 尝试重新登录Web界面获取新的令牌

2. **服务器错误（500）**：
   - 查看服务器日志（`logs/gunicorn.log`）获取详细错误信息
   - 重启EVM钱包系统（`./start_wallet.sh`）
   - 检查服务器是否有足够的资源运行

3. **连接问题**：
   - 确认EVM托管钱包系统和MCP服务器正在运行
   - 检查网络连接，确保Cherry Studio可以访问本地MCP服务器
   - 如果使用WebSocket连接失败，尝试切换到SSE连接方式

4. **消息处理错误**：
   - 确保消息格式正确
   - 检查是否有足够的权限执行请求的操作
   - 查看服务器日志获取详细错误信息

## 安全注意事项

- 定期更新您的JWT令牌
- 不要在公共环境中暴露您的配置文件
- 对于生产环境，建议使用HTTPS和WSS协议
- 在执行转账操作前，始终确认交易详情
- 避免在URL参数中传递敏感信息，如果可能，优先使用请求头或环境变量
