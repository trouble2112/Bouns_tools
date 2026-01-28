#!/bin/bash
# 访问日志分析脚本

LOG_FILE="access.log"

# 检查日志文件是否存在
if [ ! -f "$LOG_FILE" ]; then
    echo "错误: 日志文件 $LOG_FILE 不存在"
    exit 1
fi

echo "=========================="
echo "  奖金计算器访问日志分析"
echo "=========================="

# 总访问量
echo "📊 总访问次数:"
wc -l < "$LOG_FILE"

# 独立IP数量
echo -e "\n📍 独立访客数:"
cat "$LOG_FILE" | jq -r '.client_ip' | sort -u | wc -l

# 设备类型统计
echo -e "\n📱 访问设备统计:"
cat "$LOG_FILE" | jq -r '.user_agent' | while IFS= read -r ua; do
    case "$ua" in
        *"Android"*) echo "Android" ;;
        *"iPhone"*|*"iPad"*) echo "iOS" ;;
        *"Windows"*) echo "Windows" ;;
        *"Macintosh"*|*"Mac OS X"*) echo "Mac" ;;
        *"Linux"*) echo "Linux" ;;
        *) echo "Other" ;;
    esac
done | sort | uniq -c | sort -nr

# 访问时间分布
echo -e "\n🕐 访问时间分布 (按小时):"
cat "$LOG_FILE" | jq -r '.timestamp' | cut -d'T' -f2 | cut -d':' -f1 | sort | uniq -c | sort -k2n

# 最近10次访问
echo -e "\n🔍 最近10次访问:"
tail -10 "$LOG_FILE" | jq -r '"\(.timestamp) \(.client_ip) \(.path)"' | while read line; do
    echo "  $line"
done

# 独立IP列表
echo -e "\n🌐 访客IP列表:"
cat "$LOG_FILE" | jq -r '.client_ip' | sort -u | while read ip; do
    count=$(cat "$LOG_FILE" | jq -r --arg ip "$ip" 'select(.client_ip == $ip)' | wc -l)
    first_visit=$(cat "$LOG_FILE" | jq -r --arg ip "$ip" 'select(.client_ip == $ip) | .timestamp' | head -1)
    echo "  $ip (访问${count}次, 首次: $first_visit)"
done