#!/bin/bash
# 奖金计算器 Web 服务守护脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT=${1:-8080}
LOG_FILE="bonus_web.log"
PID_FILE="bonus_web.pid"

# 启动函数
start_server() {
    echo "[$(date)] 启动奖金计算器服务，端口: $PORT"
    
    # 检查端口是否被占用
    if lsof -i:$PORT > /dev/null 2>&1; then
        echo "错误: 端口 $PORT 已被占用"
        exit 1
    fi
    
    # 启动服务并保存PID
    nohup python3 server.py $PORT > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    echo "服务已启动，PID: $(cat $PID_FILE)"
    echo "日志文件: $LOG_FILE"
    echo "访问地址: http://localhost:$PORT"
}

# 停止函数
stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID > /dev/null 2>&1; then
            kill $PID
            rm "$PID_FILE"
            echo "服务已停止"
        else
            echo "服务未运行"
            rm -f "$PID_FILE"
        fi
    else
        echo "服务未运行或PID文件不存在"
    fi
}

# 重启函数
restart_server() {
    stop_server
    sleep 2
    start_server
}

# 状态检查
status_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID > /dev/null 2>&1; then
            echo "服务运行中，PID: $PID"
            echo "监听端口: $PORT"
        else
            echo "服务已停止（PID文件存在但进程不存在）"
        fi
    else
        echo "服务未运行"
    fi
}

# 守护模式 - 自动重启
daemon_mode() {
    echo "启动守护模式..."
    while true; do
        if [ ! -f "$PID_FILE" ] || ! kill -0 $(cat "$PID_FILE") > /dev/null 2>&1; then
            echo "[$(date)] 检测到服务异常，重新启动..."
            start_server
        fi
        sleep 30  # 每30秒检查一次
    done
}

case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        status_server
        ;;
    daemon)
        daemon_mode
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|daemon} [端口号]"
        echo "示例:"
        echo "  $0 start 8080     # 启动服务"
        echo "  $0 daemon 8080    # 守护模式启动"
        echo "  $0 status         # 查看状态"
        echo "  $0 stop           # 停止服务"
        exit 1
        ;;
esac