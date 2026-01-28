#!/bin/bash
# Docker 容器化部署脚本

# 构建镜像
docker_build() {
    echo "构建Docker镜像..."
    docker build -t bonus-calculator:latest .
}

# 运行容器
docker_run() {
    PORT=${1:-8080}
    echo "启动容器，端口映射: $PORT"
    
    docker run -d \
        --name bonus-calculator \
        --restart unless-stopped \
        -p $PORT:8080 \
        -v $(pwd)/logs:/app/logs \
        bonus-calculator:latest
        
    echo "容器已启动"
    echo "访问地址: http://localhost:$PORT"
}

# 停止容器
docker_stop() {
    echo "停止容器..."
    docker stop bonus-calculator
    docker rm bonus-calculator
}

# 查看日志
docker_logs() {
    docker logs -f bonus-calculator
}

case "$1" in
    build)
        docker_build
        ;;
    run)
        docker_run $2
        ;;
    stop)
        docker_stop
        ;;
    logs)
        docker_logs
        ;;
    restart)
        docker_stop
        sleep 2
        docker_run $2
        ;;
    *)
        echo "用法: $0 {build|run|stop|restart|logs} [端口号]"
        exit 1
        ;;
esac