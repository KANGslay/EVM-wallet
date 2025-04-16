#!/bin/bash

# 项目根目录
PROJECT_DIR="/Users/apple/Pyfile/evm_wallet"

# 进入项目目录
cd "$PROJECT_DIR" || exit 1

# 日志文件路径
LOG_FILE="$PROJECT_DIR/mcp_server.log"
STDIO_LOG_FILE="$PROJECT_DIR/mcp_stdio.log"
NODE_LOG_FILE="$PROJECT_DIR/mcp_node.log"

# 使用Anaconda环境中的Python解释器
PYTHON_PATH="/Users/apple/anaconda3/envs/web3/bin/python"

# MCP服务器端口
MCP_PORT=8765

# 判断各服务是否已经在运行
MCP_PID=$(ps aux | grep "app.ai.mcp_server" | grep -v grep | awk '{print $2}')
STDIO_PID=$(ps aux | grep "app.ai.mcp_stdio_adapter" | grep -v grep | awk '{print $2}')
NPX_PID=$(ps aux | grep "evm-wallet-mcp" | grep -v grep | awk '{print $2}')

# 如果所有服务都在运行，则退出
if [ -n "$MCP_PID" ] && [ -n "$STDIO_PID" ] && [ -n "$NPX_PID" ]; then
  echo "所有MCP服务已在运行:"
  echo "- MCP Server PID: $MCP_PID"
  echo "- MCP STDIO适配器 PID: $STDIO_PID"
  echo "- Node.js MCP服务 PID: $NPX_PID"
  exit 0
fi

# 检查端口是否被占用
PORT_PID=$(lsof -ti:$MCP_PORT)
if [ -n "$PORT_PID" ]; then
  echo "端口 $MCP_PORT 已被进程 $PORT_PID 占用，正在尝试终止该进程..."
  kill -9 $PORT_PID
  sleep 1
  # 再次检查端口是否已释放
  if lsof -ti:$MCP_PORT > /dev/null; then
    echo "❌ 无法释放端口 $MCP_PORT，请手动终止占用该端口的进程"
    exit 1
  else
    echo "✅ 端口 $MCP_PORT 已成功释放"
  fi
fi

# 清空日志文件
echo "" > "$LOG_FILE"

# 启动MCP Server服务
if [ -z "$MCP_PID" ]; then
  echo "正在启动 MCP Server..."
  $PYTHON_PATH -m app.ai.mcp_server > "$LOG_FILE" 2>&1 &
  MCP_PID=$!
  
  # 确保进程已启动
  sleep 2
  
  # 检查进程是否存在
  if ps -p $MCP_PID > /dev/null; then
    echo "✅ MCP Server 启动成功，PID: $MCP_PID"
    echo "📄 日志记录于: $LOG_FILE"
  else
    echo "❌ MCP Server 启动失败，请检查日志文件"
    cat "$LOG_FILE"
    exit 1
  fi
else
  echo "MCP Server 已在运行，PID: $MCP_PID"
fi

# 启动MCP STDIO适配器
if [ -z "$STDIO_PID" ]; then
  echo "正在启动 MCP STDIO适配器..."
  $PYTHON_PATH -m app.ai.mcp_stdio_adapter > "$STDIO_LOG_FILE" 2>&1 &
  STDIO_PID=$!
  
  # 确保进程已启动
  sleep 2
  
  # 检查进程是否存在
  if ps -p $STDIO_PID > /dev/null; then
    echo "✅ MCP STDIO适配器启动成功，PID: $STDIO_PID"
    echo "📄 日志记录于: $STDIO_LOG_FILE"
  else
    echo "❌ MCP STDIO适配器启动失败，请检查日志文件"
    cat "$STDIO_LOG_FILE"
  fi
else
  echo "MCP STDIO适配器已在运行，PID: $STDIO_PID"
fi

# 启动Node.js MCP服务
if [ -z "$NPX_PID" ]; then
  echo "正在启动 Node.js MCP 服务..."
  cd "$PROJECT_DIR/evm-wallet-mcp" || exit 1
  npx evm-wallet-mcp > "$NODE_LOG_FILE" 2>&1 &
  NPX_PID=$!
  
  # 确保进程已启动
  sleep 2
  
  # 检查进程是否存在
  if ps -p $NPX_PID > /dev/null; then
    echo "✅ Node.js MCP 服务启动成功，PID: $NPX_PID"
    echo "📄 日志记录于: $NODE_LOG_FILE"
  else
    echo "❌ Node.js MCP 服务启动失败，请检查日志文件"
    cat "$NODE_LOG_FILE"
  fi
  
  # 返回项目根目录
  cd "$PROJECT_DIR" || exit 1
else
  echo "Node.js MCP 服务已在运行，PID: $NPX_PID"
fi

echo "✅ 所有MCP服务已成功启动"
echo "- MCP Server: $MCP_PID"
echo "- MCP STDIO适配器: $STDIO_PID"
echo "- Node.js MCP服务: $NPX_PID"
