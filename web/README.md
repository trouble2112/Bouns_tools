# 2026上半年奖金计算器 - 部署说明

## 📦 文件清单

```
bonus_web/
├── index.html    # 主页面（核心文件）
├── server.py     # Python服务器脚本
├── start.bat     # Windows启动脚本
├── start.sh      # Linux/Mac启动脚本
└── README.md     # 本说明文档
```

## 🚀 部署方式

### 方式1：Python内置服务器（推荐测试用）

```bash
# 默认8080端口
python server.py

# 自定义端口
python server.py 3000
```

### 方式2：Nginx部署（推荐生产环境）

1. 将 `index.html` 放到 Nginx 网站目录
2. Nginx 配置示例：

```nginx
server {
    listen 80;
    server_name bonus.example.com;
    
    root /var/www/bonus_web;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # 启用gzip压缩
    gzip on;
    gzip_types text/html text/css application/javascript;
}
```

### 方式3：Docker部署

创建 `Dockerfile`：

```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
EXPOSE 80
```

构建并运行：

```bash
docker build -t bonus-calculator .
docker run -d -p 8080:80 bonus-calculator
```

### 方式4：静态托管服务

直接上传 `index.html` 到以下平台：
- GitHub Pages
- Vercel
- Netlify
- 阿里云OSS
- 腾讯云COS

## 📱 访问地址

- 本地：`http://localhost:8080`
- 局域网：`http://服务器IP:8080`
- 公网：`http://域名` (需配置DNS)

## ⚠️ 注意事项

1. **数据存储**：数据保存在浏览器 localStorage，不同设备/浏览器数据不共享
2. **HTTPS**：生产环境建议启用HTTPS
3. **备份**：重要数据请使用「导出数据」功能定期备份

## 🔧 常见问题

**Q: 手机无法访问？**
- 确保手机和服务器在同一网络
- 检查防火墙是否开放端口
- 使用服务器的局域网IP而非localhost

**Q: 数据丢失？**
- 清除浏览器缓存会导致数据丢失
- 建议定期使用导出功能备份数据
