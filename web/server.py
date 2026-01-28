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

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # 添加CORS支持
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"=" * 50)
        print(f"🚀 奖金计算器服务已启动")
        print(f"=" * 50)
        print(f"📍 本地访问: http://localhost:{PORT}")
        print(f"📍 局域网访问: http://0.0.0.0:{PORT}")
        print(f"=" * 50)
        print(f"按 Ctrl+C 停止服务")
        print(f"=" * 50)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务已停止")
