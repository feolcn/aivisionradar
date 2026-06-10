# 群晖 Synology NAS 部署指南

适用于 DS923+（及其他支持 Container Manager 的 DSM 7.x 机型）。

部署完成后通过 Cloudflare Tunnel 实现外网 HTTPS 访问，无需开放路由器端口，无需公网 IP。

---

## 架构

```
DS923+ (Container Manager)
├── aivisionradar   → FastAPI + 定时抓取
└── cloudflared     → Cloudflare Tunnel 内网穿透

外网用户 → radar.yourdomain.com → Cloudflare → cloudflared → aivisionradar
```

---

## 第一步：DSM 准备工作

### 1.1 安装 Container Manager
DSM → 套件中心 → 搜索 "Container Manager" → 安装

### 1.2 开启 SSH
DSM → 控制面板 → 终端机和 SNMP → 勾选「启动 SSH 功能」→ 应用

### 1.3 SSH 登录 NAS
```bash
ssh 你的用户名@NAS的局域网IP
# 例如：ssh admin@192.168.1.100
```

---

## 第二步：Cloudflare Tunnel 配置

### 2.1 创建 Tunnel

1. 打开 [Cloudflare Zero Trust](https://one.dash.cloudflare.com/)
2. 左侧菜单 → **Networks → Tunnels**
3. 点击 **Create a tunnel**
4. 选择 **Cloudflared** → Next
5. Tunnel name 填写：`aivisionradar`
6. 点击 **Save tunnel**
7. 在 "Install and run a connector" 页面，选择 **Docker**
8. 复制命令中的 token（`--token` 后面那串很长的字符串）

### 2.2 配置公开域名

在 Tunnel 创建完成后的 "Public Hostname" 页面：

| 字段 | 填写 |
|---|---|
| Subdomain | `radar` |
| Domain | 你的域名（例如 `example.com`） |
| Type | HTTP |
| URL | `aivisionradar:8000` |

点击 **Save tunnel**。

> Cloudflare 会自动在 DNS 中添加对应的 CNAME 记录，无需手动操作。

---

## 第三步：部署到 NAS

### 3.1 在 NAS 上创建目录并克隆项目

```bash
# SSH 登录后执行
sudo mkdir -p /volume1/docker/aivisionradar
cd /volume1/docker/aivisionradar
sudo git clone https://github.com/feolcn/aivisionradar.git .
sudo mkdir -p data
```

### 3.2 配置环境变量

```bash
sudo cp .env.example .env
sudo vi .env
```

将以下内容填入 `.env`：

```env
APP_NAME=AIVisionRadar
DATABASE_URL=sqlite:///./data/aivisionradar.db
ENABLE_SCHEDULER=true

# 第二步复制的 Tunnel Token
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoixxxxxxxx...

# 可选：GitHub Token（用于 GitHub Search）
GITHUB_TOKEN=

# 可选：AI 摘要
AI_BASE_URL=
AI_API_KEY=
AI_MODEL=gpt-4o-mini

CRAWL_INTERVAL_HOURS=6
DAILY_REPORT_HOUR=8
```

### 3.3 启动服务

```bash
cd /volume1/docker/aivisionradar
sudo docker compose -f docker-compose.synology.yml up -d --build
```

首次启动会构建镜像，需要 3-5 分钟。

### 3.4 查看启动日志

```bash
sudo docker logs aivisionradar -f
```

看到以下日志说明启动成功：
```
Application startup complete.
```

### 3.5 执行首次数据初始化

```bash
sudo docker exec aivisionradar python -m app.cli seed
sudo docker exec aivisionradar python -m app.cli crawl
```

首次抓取约需 2-5 分钟。

---

## 第四步：验证访问

- **局域网访问**（直接）：`http://NAS局域网IP:8000`
- **外网访问**（Tunnel）：`https://radar.yourdomain.com`

外网地址约 1-2 分钟后生效（等 Cloudflare DNS 同步）。

---

## 日常操作

### 查看运行状态
```bash
sudo docker ps | grep aivisionradar
```

### 手动触发抓取
```bash
sudo docker exec aivisionradar python -m app.cli crawl
```

### 查看今日日报
```bash
sudo docker exec aivisionradar python -m app.cli report
```

### 更新到最新版本
```bash
cd /volume1/docker/aivisionradar
sudo git pull
sudo docker compose -f docker-compose.synology.yml up -d --build
```

### 停止服务
```bash
sudo docker compose -f docker-compose.synology.yml down
```

---

## 可选：添加访问密码（推荐）

由于没有登录系统，建议在 Cloudflare 层加访问控制：

1. Cloudflare Zero Trust → **Access → Applications**
2. 点击 **Add an application → Self-hosted**
3. Application name: `AIVisionRadar`
4. Application domain: `radar.yourdomain.com`
5. 配置 Policy → 添加邮箱白名单或 One-Time PIN

这样访问时会先验证邮箱，安全且免费。

---

## 故障排查

### Tunnel 连接失败
```bash
sudo docker logs aivisionradar-tunnel
```
检查 `CLOUDFLARE_TUNNEL_TOKEN` 是否正确复制。

### 应用启动失败
```bash
sudo docker logs aivisionradar
```
常见原因：data 目录权限问题，执行 `sudo chmod -R 777 /volume1/docker/aivisionradar/data`

### 抓取失败
部分 RSS 源（如 Hugging Face Daily Papers）格式偶尔异常，属正常现象，不影响其他源。
