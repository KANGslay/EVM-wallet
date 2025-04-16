#!/bin/bash

echo "正在尝试关闭 MCP 相关服务..."

# 项目根目录
PROJECT_DIR="/Users/apple/Pyfile/evm_wallet"

# 日志文件
LOG_FILE="$PROJECT_DIR/stop_mcp.log"
echo "" > "$LOG_FILE"

# 获取所有 mcp_server 相关进程的 PID
MCP_PIDS=$(ps aux | grep "app.ai.mcp_server" | grep -v grep | awk '{print $2}')

# 获取所有 mcp_stdio_adapter 相关进程的 PID
STDIO_PIDS=$(ps aux | grep "app.ai.mcp_stdio_adapter" | grep -v grep | awk '{print $2}')

# 获取所有 evm-wallet-mcp 相关进程的 PID
NPX_PIDS=$(ps aux | grep "evm-wallet-mcp" | grep -v grep | awk '{print $2}')

# 获取所有 uvicorn 相关的 MCP 进程的 PID
UVICORN_PIDS=$(ps aux | grep "uvicorn" | grep "app.ai.mcp_server:app" | grep -v grep | awk '{print $2}')

# 合并所有 PID
PIDS="$MCP_PIDS $STDIO_PIDS $NPX_PIDS $UVICORN_PIDS"

if [ -n "$PIDS" ]; then
  echo "找到以下MCP相关进程:"
  
  # 分类显示进程
  if [ -n "$MCP_PIDS" ]; then
    echo "- MCP Server: $MCP_PIDS"
  fi
  
  if [ -n "$STDIO_PIDS" ]; then
    echo "- MCP STDIO适配器: $STDIO_PIDS"
  fi
  
  if [ -n "$NPX_PIDS" ]; then
    echo "- Node.js MCP服务: $NPX_PIDS"
  fi
  
  if [ -n "$UVICORN_PIDS" ]; then
    echo "- Uvicorn服务: $UVICORN_PIDS"
  fi
  
  # 终止所有进程
  for PID in $PIDS; do
    kill -9 "$PID" >> "$LOG_FILE" 2>&1
    echo "已结束进程 PID: $PID"
    
    # 验证进程是否已终止
    sleep 0.5
    if ps -p "$PID" > /dev/null 2>&1; then
      echo "⚠️ 进程 $PID 可能未成功终止，再次尝试..."
      kill -9 "$PID" >> "$LOG_FILE" 2>&1
    fi
  done
  
  # 最终确认
  REMAINING=$(ps aux | grep -E "app.ai.mcp_server|app.ai.mcp_stdio_adapter|evm-wallet-mcp" | grep -v grep | awk '{print $2}')
  if [ -n "$REMAINING" ]; then
    echo "⚠️ 仍有MCP相关进程在运行: $REMAINING"
    echo "请手动检查并终止这些进程"
  else
    echo "✅ 所有MCP相关服务已完全停止"
  fi
else
  echo "未发现任何MCP相关服务正在运行"
fi

echo "MCP服务停止操作完成"
