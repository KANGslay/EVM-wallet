#!/bin/bash

APP_NAME="EVM Wallet 系统"
API_PORT=8081
LOGS_DIR="logs"
GUNICORN_CMD="gunicorn -w 1 -k uvicorn.workers.UvicornWorker app.main:app"
NGINX_CHECK_URL="http://localhost/health"

# 初始化日志目录
mkdir -p ${LOGS_DIR}
touch ${LOGS_DIR}/gunicorn.log

echo "🔄 正在启动 ${APP_NAME}..."

# 资源清理函数
clean_resources() {
    echo "🔍 清理系统残留资源..."
    
    # 多阶段进程终止
    for signal in 15 2 3 9; do
        pkill -${signal} -f "${GUNICORN_CMD}" >/dev/null 2>&1 && sleep 2
    done
    
    # 端口强制释放
    if lsof -ti :${API_PORT} >/dev/null; then
        echo "⚠️  强制释放端口 ${API_PORT}"
        lsof -ti :${API_PORT} | xargs kill -9 >/dev/null 2>&1
    fi
    
    # 清理 UNIX 套接字
    find /tmp -name 'gunicorn*.sock' -delete 2>/dev/null
}

# 系统资源检查
check_system() {
    echo "🔍 检查系统资源..."
    
    # 内存检查（MacOS兼容）
    if [[ "$OSTYPE" == "darwin"* ]]; then
        free_mem=$(top -l 1 | grep PhysMem | awk '{print $6}' | tr -d 'M')
    else
        free_mem=$(free -m | awk '/Mem:/ {print $7}')
    fi
    
    if [ ${free_mem} -lt 512 ]; then
        echo "⚠️  警告：可用内存低于 512MB (当前: ${free_mem}MB)"
        echo "尝试释放内存..."
        sudo purge  # macOS
        [ -x "$(command -v sync)" ] && sync && echo 3 > /proc/sys/vm/drop_caches  # Linux
        sleep 3
    fi
}

# 启动状态验证
check_service() {
    local url=$1
    local max_retry=10
    local retry=0
    
    until curl -sf --connect-timeout 5 "${url}" > /dev/null; do
        sleep 3
        
        if [ ${retry} -eq ${max_retry} ]; then
            echo "❌ 服务启动失败! 错误日志："
            tail -n 50 ${LOGS_DIR}/gunicorn.log
            exit 1
        fi
        
        local retry=$((retry + 1))
        echo "⏳ 等待服务响应... (${retry}/${max_retry})"
    done
}

# 主流程
main() {
    clean_resources
    check_system

    # 启动后端服务
    echo "🚀 启动后端服务 (Gunicorn)..."
    nohup ${GUNICORN_CMD} \
        --bind 0.0.0.0:${API_PORT} \
        --timeout 120 \
        --graceful-timeout 30 \
        --max-requests 1000 \
        > ${LOGS_DIR}/gunicorn.log 2>&1 &
    
    GUNICORN_PID=$!
    echo "✅ Gunicorn 实例创建 PID: ${GUNICORN_PID}"
    
    # 启动确认
    check_service "http://localhost:${API_PORT}/health"

    # NGINX 管理
    echo "🌐 配置 Web 接入层..."
    if command -v brew &> /dev/null; then
        brew services restart nginx
        check_service "${NGINX_CHECK_URL}"
    else
        echo "⚠️  未检测到 Homebrew，跳过 Nginx 管理"
    fi

    # 状态展示
    echo -e "\n🎉 系统启动成功！"
    echo "--------------------------------------------"
    echo "管理端点 ➔ http://localhost:${API_PORT}/docs"
    echo "用户访问 ➔ http://localhost"
    echo "实时日志 ➔ tail -f ${LOGS_DIR}/gunicorn.log"
    echo "--------------------------------------------"
}

# 执行主流程并捕获异常
main || {
    echo -e "\n❌ 启动过程中发生致命错误!"
    echo "⚠️  推荐故障排查步骤："
    echo "1. 检查端口占用：lsof -i :${API_PORT}"
    echo "2. 查看完整日志：less ${LOGS_DIR}/gunicorn.log"
    echo "3. 尝试手工启动：${GUNICORN_CMD}"
    exit 1
}
