# Claude Desktop MCP协议配置指南

本文档提供了如何在Claude Desktop中配置MCP协议以连接EVM托管钱包系统的详细说明。

## 什么是MCP协议

MCP (Model Control Protocol) 是一种允许Claude等AI助手与外部系统进行通信的协议。在本项目中，MCP协议使Claude Desktop能够与EVM托管钱包系统进行交互，执行查询余额、发起转账等操作。

## 配置步骤

### 1. 确保MCP服务器已启动

在配置Claude Desktop之前，请确保EVM托管钱包系统的MCP服务器已经启动：

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

### 3. 创建MCP配置文件

Claude Desktop需要一个JSON格式的配置文件。您可以使用项目中提供的示例文件`claude_mcp_config.json`，或创建一个新文件。

#### WebSocket连接配置

```json
{
  "name": "EVM托管钱包",
  "description": "通过Claude Desktop操作EVM托管钱包系统",
  "version": "1.0.0",
  "protocol": "mcp",
  "connection": {
    "server_url": "ws://localhost:8081/mcp/ws",
    "auth": {
      "type": "bearer",
      "token": "YOUR_JWT_TOKEN_HERE"
    }
  },
  "capabilities": [
    "wallet_query",
    "transaction_create",
    "balance_check"
  ],
  "settings": {
    "auto_connect": true,
    "timeout_seconds": 30,
    "retry_attempts": 3
  }
}
```

#### SSE连接配置（推荐）

```json
{
  "name": "EVM托管钱包",
  "description": "通过Claude Desktop操作EVM托管钱包系统",
  "version": "1.0.0",
  "protocol": "mcp",
  "connection": {
    "server_url": "http://localhost:8081/mcp/sse?AUTH_TOKEN=YOUR_JWT_TOKEN_HERE",
    "message_endpoint": "http://localhost:8081/mcp/sse/message?AUTH_TOKEN=YOUR_JWT_TOKEN_HERE",
    "connection_type": "sse",
    "auth": {
      "type": "bearer",
      "token": "YOUR_JWT_TOKEN_HERE"
    }
  },
  "capabilities": [
    "wallet_query",
    "transaction_create",
    "balance_check"
  ],
  "settings": {
    "auto_connect": true,
    "timeout_seconds": 30,
    "retry_attempts": 3
  }
}
```

请将`YOUR_JWT_TOKEN_HERE`替换为您在上一步获取的实际JWT令牌。

> **注意**：使用SSE配置时，请将认证令牌直接作为URL参数添加到`server_url`和`message_endpoint`中，这样可以避免认证问题。

### 4. 在Claude Desktop中配置MCP连接

1. 打开Claude Desktop应用程序
2. 点击右上角的设置图标，进入设置页面
3. 找到并点击"MCP连接"或"扩展"选项
4. 点击"添加新连接"或"导入配置"
5. 选择您创建的JSON配置文件
6. 点击"保存"并按提示重启Claude Desktop

## 使用Claude操作钱包

配置完成后，您可以在Claude Desktop中使用自然语言与Claude交流，执行以下操作：

- 查询钱包余额："查询我的ETH余额"
- 发起转账："转0.01 ETH到0x123..."
- 查询交易历史："显示我最近的交易记录"

Claude将通过MCP协议与钱包系统交互，执行相应操作并返回结果。

## 故障排除

如果连接失败，请检查：

1. **认证错误（401）**：
   - 确保JWT令牌有效且未过期
   - 对于SSE连接，确保令牌已作为URL参数添加到`server_url`和`message_endpoint`中
   - 尝试重新登录Web界面获取新的令牌

2. **服务器错误（500）**：
   - 查看服务器日志（`logs/gunicorn.log`）获取详细错误信息
   - 重启EVM钱包系统（`./start_wallet.sh`）
   - 检查服务器是否有足够的资源运行

3. **连接问题**：
   - 确认EVM托管钱包系统和MCP服务器正在运行
   - 检查网络连接，确保Claude Desktop可以访问本地MCP服务器
   - 如果使用WebSocket连接失败，尝试切换到SSE连接方式

4. **消息处理错误**：
   - 确保消息格式正确
   - 检查是否有足够的权限执行请求的操作
   - 查看服务器日志获取详细错误信息

如需更多帮助，请参考项目文档或联系开发团队。