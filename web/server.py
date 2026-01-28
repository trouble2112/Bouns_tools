#!/usr/bin/env python3
"""
奖金计算器 Web 服务器
启动方式: python server.py [端口号]
默认端口: 8080
"""

import http.server
import socketserver
import os
import sys
import json
import datetime
from urllib.parse import urlparse, parse_qs

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(DIRECTORY, 'access.log')

def log_request(client_ip, method, path, user_agent, referer="", status_code=200):
    """记录详细的访问日志"""
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "client_ip": client_ip,
        "method": method,
        "path": path,
        "user_agent": user_agent,
        "referer": referer,
        "status_code": status_code
    }
    
    # 写入JSON格式日志
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    # 控制台输出简化信息
    device_type = get_device_type(user_agent)
    print(f"[{log_entry['timestamp']}] {client_ip} - {method} {path} - {device_type}")

def get_device_type(user_agent):
    """根据User-Agent判断设备类型"""
    ua = user_agent.lower()
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        if 'android' in ua:
            return "📱 Android"
        elif 'iphone' in ua or 'ipad' in ua:
            return "📱 iOS"
        else:
            return "📱 Mobile"
    elif 'windows' in ua:
        return "💻 Windows"
    elif 'macintosh' in ua or 'mac os x' in ua:
        return "💻 Mac"
    elif 'linux' in ua:
        return "💻 Linux"
    else:
        return "🖥️ Unknown"

class LoggingHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def log_message(self, format, *args):
        """重写日志方法，不输出默认日志"""
        pass
    
    def do_GET(self):
        """处理GET请求并记录详细信息"""
        client_ip = self.get_client_ip()
        user_agent = self.headers.get('User-Agent', '')
        referer = self.headers.get('Referer', '')
        
        # 调用父类方法处理请求
        super().do_GET()
        
        # 记录访问日志
        log_request(client_ip, "GET", self.path, user_agent, referer)
    
    def do_POST(self):
        """处理POST请求"""
        client_ip = self.get_client_ip()
        user_agent = self.headers.get('User-Agent', '')
        referer = self.headers.get('Referer', '')
        
        super().do_POST()
        log_request(client_ip, "POST", self.path, user_agent, referer)
    
    def get_client_ip(self):
        """获取客户端真实IP"""
        # 检查代理头
        forwarded_for = self.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = self.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # 返回直接连接的IP
        return self.client_address[0]
    
    def end_headers(self):
        # 添加CORS支持
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

if __name__ == '__main__':
    # 创建日志文件
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write("")
    
    with socketserver.TCPServer(("", PORT), LoggingHandler) as httpd:
        print(f"=" * 50)
        print(f"🚀 奖金计算器服务已启动")
        print(f"=" * 50)
        print(f"📍 本地访问: http://localhost:{PORT}")
        print(f"📍 局域网访问: http://0.0.0.0:{PORT}")
        print(f"📊 访问日志: {LOG_FILE}")
        print(f"=" * 50)
        print(f"按 Ctrl+C 停止服务")
        print(f"=" * 50)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务已停止")
