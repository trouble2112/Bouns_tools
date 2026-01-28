#!/bin/bash
# 奖金计算器 Web 服务启动脚本 (Linux/Mac)

PORT=${1:-8080}

echo "========================================"
echo "   奖金计算器 Web 服务启动"
echo "========================================"
echo ""

python3 server.py $PORT
