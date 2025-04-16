# EVM钱包MCP连接器

这个包提供了一个连接Cherry Studio和EVM钱包系统的MCP接口。

## 保姆级启动指南

### 第一步：准备环境

确保您已安装Node.js和npm。如果没有，请先安装：
- 访问 [Node.js官网](https://nodejs.org/) 下载并安装最新的LTS版本
- 安装完成后，打开终端验证安装：
  ```bash
  node -v
  npm -v
  ```

### 第二步：安装MCP包

有两种方式安装EVM钱包MCP连接器：

**方式1：全局安装（推荐）**
```bash
# 进入evm-wallet-mcp目录
cd /Users/apple/Pyfile/evm_wallet/evm-wallet-mcp

# 链接到全局
npm link
```

**方式2：使用npx直接运行**
```bash
# 进入evm-wallet-mcp目录
cd /Users/apple/Pyfile/evm_wallet/evm-wallet-mcp

# 使用npx运行
npx .
```

### 第三步：启动Python MCP服务器

```bash
# 进入项目根目录
cd /Users/apple/Pyfile/evm_wallet

# 启动MCP服务器
python -m app.ai.mcp_server
```

### 第四步：配置Cherry Studio

在Cherry Studio中配置MCP服务器时，使用以下配置：

```json
{
  "mcpServers": {
    "EVM_Wallet_MCP_12345": {
      "name": "EVM钱包MCP服务",
      "description": "连接到EVM钱包系统的MCP服务",
      "baseUrl": "",
      "command": "npx",
      "args": ["evm-wallet-mcp"],
      "protocol": "stdio",
      "timeoutMs": 300000,
      "env": {},
      "isActive": true
    }
  }
}
```

### 第五步：验证连接

在Cherry Studio中添加MCP服务器配置后，点击“测试连接”按钮。如果连接成功，将显示“连接成功”的提示。

## 故障排除

### 常见错误及解决方法

1. **启动失败：Error invoking remote method 'mcp:list-tools': Error: Not connected**
   - 确保 Python MCP服务器正在运行
   - 检查配置文件中的命令和参数是否正确
   - 尝试增加 timeoutMs 值，例如设置为 300000 (5分钟)

2. **连接关闭：Connection closed**
   - 检查 Python 服务器是否已经崩溃
   - 查看服务器日志中是否有错误信息
   - 确保服务器能够处理 JSON-RPC 格式的请求

3. **用户不存在：用户 admin 不存在**
   - 在 mcp-server-fetch.py 中添加对默认用户的处理
   - 确保使用正确的认证令牌

### 测试方法

如果遇到问题，可以尝试以下测试方法：

```bash
# 手动测试MCP服务器响应
echo '{"jsonrpc": "2.0", "id": 1, "method": "mcp:list-tools"}' | python -m app.ai.mcp_server
```

## 功能

- 查询钱包余额
- 发送交易
- 查询交易历史
- 导入代币

## 开发

```bash
# 链接到全局
npm link

# 运行
evm-wallet-mcp
```
