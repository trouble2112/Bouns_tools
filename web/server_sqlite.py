#!/usr/bin/env python3
"""
奖金计算器 Web 服务器 - SQLite版本
支持数据持久化和API接口
"""

import http.server
import socketserver
import os
import sys
import json
import sqlite3
import datetime
import urllib.parse
from http import HTTPStatus
from typing import Dict, List, Any

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DIRECTORY, 'bonus_data.db')
LOG_FILE = os.path.join(DIRECTORY, 'access.log')

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS persons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    region TEXT,
                    org TEXT,
                    revenue TEXT,  -- JSON string for monthly revenue
                    company_revenue REAL DEFAULT 0,
                    target REAL DEFAULT 0,
                    collection_rate REAL DEFAULT 0.9,
                    ratio REAL,
                    region_90 INTEGER DEFAULT 0,
                    region_100 INTEGER DEFAULT 0,
                    national_90 INTEGER DEFAULT 0,
                    national_100 INTEGER DEFAULT 0,
                    ceo_bonus REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS params (
                    id INTEGER PRIMARY KEY,
                    coefficients TEXT,  -- JSON string for time coefficients
                    threshold_90 REAL DEFAULT 0.85,
                    threshold_100 REAL DEFAULT 0.90,
                    dm_mode TEXT DEFAULT 'exclusive',
                    other_mode TEXT DEFAULT 'stack',
                    cp_subsidy REAL DEFAULT 60000,
                    sales_subsidy REAL DEFAULT 800,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 插入默认参数（如果不存在）
            conn.execute("""
                INSERT OR IGNORE INTO params (id, coefficients) 
                VALUES (1, '[1.15, 1.15, 1.10, 1.00, 0.90, 0.85]')
            """)
            
            conn.commit()
    
    def get_persons(self) -> List[Dict]:
        """获取所有人员"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM persons ORDER BY created_at DESC")
            persons = []
            for row in cursor.fetchall():
                person = dict(row)
                person['revenue'] = json.loads(person['revenue'] or '[]')
                persons.append(person)
            return persons
    
    def get_person(self, person_id: int) -> Dict:
        """获取单个人员"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM persons WHERE id = ?", (person_id,))
            row = cursor.fetchone()
            if row:
                person = dict(row)
                person['revenue'] = json.loads(person['revenue'] or '[]')
                return person
            return None
    
    def create_person(self, data: Dict) -> int:
        """创建人员"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO persons (
                    name, role, region, org, revenue, company_revenue, target,
                    collection_rate, ratio, region_90, region_100,
                    national_90, national_100, ceo_bonus
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('name', ''),
                data.get('role', ''),
                data.get('region', ''),
                data.get('org', ''),
                json.dumps(data.get('revenue', [])),
                data.get('company_revenue', 0),
                data.get('target', 0),
                data.get('collection_rate', 0.9),
                data.get('ratio'),
                data.get('region_90', 0),
                data.get('region_100', 0),
                data.get('national_90', 0),
                data.get('national_100', 0),
                data.get('ceo_bonus', 0)
            ))
            conn.commit()
            return cursor.lastrowid
    
    def update_person(self, person_id: int, data: Dict) -> bool:
        """更新人员"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE persons SET
                    name = ?, role = ?, region = ?, org = ?, revenue = ?,
                    company_revenue = ?, target = ?, collection_rate = ?,
                    ratio = ?, region_90 = ?, region_100 = ?,
                    national_90 = ?, national_100 = ?, ceo_bonus = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data.get('name', ''),
                data.get('role', ''),
                data.get('region', ''),
                data.get('org', ''),
                json.dumps(data.get('revenue', [])),
                data.get('company_revenue', 0),
                data.get('target', 0),
                data.get('collection_rate', 0.9),
                data.get('ratio'),
                data.get('region_90', 0),
                data.get('region_100', 0),
                data.get('national_90', 0),
                data.get('national_100', 0),
                data.get('ceo_bonus', 0),
                person_id
            ))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_person(self, person_id: int) -> bool:
        """删除人员"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM persons WHERE id = ?", (person_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_params(self) -> Dict:
        """获取参数配置"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM params WHERE id = 1")
            row = cursor.fetchone()
            if row:
                params = dict(row)
                params['coefficients'] = json.loads(params['coefficients'])
                return params
            return self.get_default_params()
    
    def update_params(self, data: Dict) -> bool:
        """更新参数配置"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE params SET
                    coefficients = ?, threshold_90 = ?, threshold_100 = ?,
                    dm_mode = ?, other_mode = ?, cp_subsidy = ?,
                    sales_subsidy = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            """, (
                json.dumps(data.get('coefficients', [1.15, 1.15, 1.10, 1.00, 0.90, 0.85])),
                data.get('threshold_90', 0.85),
                data.get('threshold_100', 0.90),
                data.get('dm_mode', 'exclusive'),
                data.get('other_mode', 'stack'),
                data.get('cp_subsidy', 60000),
                data.get('sales_subsidy', 800)
            ))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_default_params(self) -> Dict:
        """获取默认参数"""
        return {
            'coefficients': [1.15, 1.15, 1.10, 1.00, 0.90, 0.85],
            'threshold_90': 0.85,
            'threshold_100': 0.90,
            'dm_mode': 'exclusive',
            'other_mode': 'stack',
            'cp_subsidy': 60000,
            'sales_subsidy': 800
        }

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

class BonusAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db = DatabaseManager(DB_FILE)
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def log_message(self, format, *args):
        """重写日志方法，不输出默认日志"""
        pass
    
    def do_GET(self):
        """处理GET请求"""
        client_ip = self.get_client_ip()
        user_agent = self.headers.get('User-Agent', '')
        referer = self.headers.get('Referer', '')
        
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path.startswith('/api/'):
            self.handle_api_request('GET', path, parsed_path.query)
        else:
            super().do_GET()
        
        log_request(client_ip, "GET", self.path, user_agent, referer)
    
    def do_POST(self):
        """处理POST请求"""
        client_ip = self.get_client_ip()
        user_agent = self.headers.get('User-Agent', '')
        referer = self.headers.get('Referer', '')
        
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path.startswith('/api/'):
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            self.handle_api_request('POST', path, post_data)
        else:
            super().do_POST()
        
        log_request(client_ip, "POST", self.path, user_agent, referer)
    
    def do_PUT(self):
        """处理PUT请求"""
        client_ip = self.get_client_ip()
        user_agent = self.headers.get('User-Agent', '')
        
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path.startswith('/api/'):
            content_length = int(self.headers.get('Content-Length', 0))
            put_data = self.rfile.read(content_length).decode('utf-8')
            self.handle_api_request('PUT', path, put_data)
        
        log_request(client_ip, "PUT", self.path, user_agent, "", 200)
    
    def do_DELETE(self):
        """处理DELETE请求"""
        client_ip = self.get_client_ip()
        user_agent = self.headers.get('User-Agent', '')
        
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path.startswith('/api/'):
            self.handle_api_request('DELETE', path, "")
        
        log_request(client_ip, "DELETE", self.path, user_agent, "", 200)
    
    def handle_api_request(self, method: str, path: str, data: str):
        """处理API请求"""
        try:
            if path == '/api/persons':
                if method == 'GET':
                    persons = self.db.get_persons()
                    self.send_json_response({"status": "success", "data": persons})
                elif method == 'POST':
                    post_data = json.loads(data) if data else {}
                    person_id = self.db.create_person(post_data)
                    self.send_json_response({"status": "success", "id": person_id})
            
            elif path.startswith('/api/persons/'):
                person_id = int(path.split('/')[-1])
                if method == 'GET':
                    person = self.db.get_person(person_id)
                    if person:
                        self.send_json_response({"status": "success", "data": person})
                    else:
                        self.send_json_response({"status": "error", "message": "Person not found"}, 404)
                elif method == 'PUT':
                    put_data = json.loads(data) if data else {}
                    success = self.db.update_person(person_id, put_data)
                    if success:
                        self.send_json_response({"status": "success"})
                    else:
                        self.send_json_response({"status": "error", "message": "Person not found"}, 404)
                elif method == 'DELETE':
                    success = self.db.delete_person(person_id)
                    if success:
                        self.send_json_response({"status": "success"})
                    else:
                        self.send_json_response({"status": "error", "message": "Person not found"}, 404)
            
            elif path == '/api/params':
                if method == 'GET':
                    params = self.db.get_params()
                    self.send_json_response({"status": "success", "data": params})
                elif method == 'POST':
                    params_data = json.loads(data) if data else {}
                    success = self.db.update_params(params_data)
                    self.send_json_response({"status": "success" if success else "error"})
            
            else:
                self.send_json_response({"status": "error", "message": "API endpoint not found"}, 404)
                
        except Exception as e:
            print(f"API Error: {e}")
            self.send_json_response({"status": "error", "message": str(e)}, 500)
    
    def send_json_response(self, data: Dict, status_code: int = 200):
        """发送JSON响应"""
        response = json.dumps(data, ensure_ascii=False)
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def get_client_ip(self):
        """获取客户端真实IP"""
        forwarded_for = self.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = self.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return self.client_address[0]
    
    def end_headers(self):
        # 添加CORS支持
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

if __name__ == '__main__':
    # 创建日志文件
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write("")
    
    # 初始化数据库
    db = DatabaseManager(DB_FILE)
    
    with socketserver.TCPServer(("", PORT), BonusAPIHandler) as httpd:
        print(f"=" * 60)
        print(f"🚀 奖金计算器服务已启动 (SQLite版本)")
        print(f"=" * 60)
        print(f"📍 前端访问: http://localhost:{PORT}")
        print(f"📍 局域网访问: http://0.0.0.0:{PORT}")
        print(f"💾 数据库: {DB_FILE}")
        print(f"📊 访问日志: {LOG_FILE}")
        print(f"=" * 60)
        print(f"🔌 API接口:")
        print(f"  GET    /api/persons      # 获取所有人员")
        print(f"  POST   /api/persons      # 创建人员")
        print(f"  PUT    /api/persons/{{id}} # 更新人员")
        print(f"  DELETE /api/persons/{{id}} # 删除人员")
        print(f"  GET    /api/params       # 获取参数")
        print(f"  POST   /api/params       # 更新参数")
        print(f"=" * 60)
        print(f"按 Ctrl+C 停止服务")
        print(f"=" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务已停止")