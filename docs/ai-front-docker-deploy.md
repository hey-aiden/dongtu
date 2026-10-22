# ai-front 前端部署文档

`ai-front` 是 React 19 + Create React App 前端。所有后端请求统一走**相对路径 `/dongtu`**,由代理层转发到真实后端,本地开发和线上部署共用同一套思路。

包管理器用 **pnpm**(项目根目录是 `pnpm-lock.yaml`,不要用 `npm`,`package-lock.json` 已废弃且与 `package.json` 不同步)。

## 一、两种运行方式

| 场景 | 启动方式 | 访问地址 | 代理层 |
|---|---|---|---|
| 本地开发 | `make dev`(pnpm 起 dev server) | http://localhost:3000 | CRA 的 `proxy` 字段 |
| 线上部署 | Docker(nginx 托管静态文件) | 映射端口(默认 3000) | nginx 反向代理 |

## 二、本地开发(不用 Docker)

前置:后端 ai-server 已在宿主机 `localhost:8000` 运行;已装 Node(建议 24)和 pnpm。

```bash
cd ai-front
pnpm install   # 首次或依赖变更后
make dev       # 等价于 pnpm start,起 dev server
```

`package.json` 里的 `"proxy": "http://localhost:8000"` 会把 `/dongtu/*` 转发到后端。前端 `client.js` 里 `BASE_URL = '/dongtu'`,无需改动。

## 三、线上部署(Docker)

### 1. 构建镜像

```bash
cd ai-front
make docker-build          # 等价于 docker build -t ai-front:latest .
```

构建分两阶段:`node:24-alpine` + pnpm 编译出 `build/`,再拷贝进 `nginx:alpine` 托管。

### 2. 启动

```bash
# 方式 A:Makefile(推荐)
cd ai-front
BACKEND_URL=http://你的后端地址:8000 make docker-up

# 方式 B:docker-compose 直接跑
cd ai-front
BACKEND_URL=http://你的后端地址:8000 docker-compose up -d --build

# 方式 C:docker run
docker run -d -p 3000:80 \
  -e BACKEND_URL=http://你的后端地址:8000 \
  ai-front:latest
```

启动后访问 http://localhost:3000。

### 3. 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `BACKEND_URL` | 后端 ai-server 地址,**不带末尾斜杠**,形如 `http://host:8000` | `http://host.docker.internal:8000` |

## 四、请求链路

```
浏览器 ──/dongtu/*──▶ 代理层(nginx / CRA dev server) ──▶ ai-server(端口 8000)
```

`client.js` 里 `BASE_URL = '/dongtu'`,所有请求同源相对路径,由代理层转发,彻底规避 CORS 和硬编码地址。

## 五、常用命令(Makefile)

| 命令 | 作用 |
|---|---|
| `make dev` | 本地开发,起 dev server(热更新) |
| `make install` | 安装依赖(pnpm install) |
| `make build` | 本地构建生产产物到 `build/` |
| `make docker-build` | 构建线上镜像 |
| `make docker-up` | 起线上容器(含重新构建) |
| `make docker-down` | 停掉线上容器 |

## 六、常见问题

### 1. 容器里连不到后端(connection refused / 502)
- **Mac/Windows(Docker Desktop)**:默认 `BACKEND_URL=http://host.docker.internal:8000` 即可,`host.docker.internal` 指宿主机。
- **Linux**:给 compose 服务加 `extra_hosts: ["host.docker.internal:host-gateway"]`,或直接把 `BACKEND_URL` 写成宿主机局域网 IP。
- 确认后端确实监听 `8000`,且 `/dongtu` 前缀存在。

### 2. nginx 启动即报 `host not found in upstream`
`BACKEND_URL` 必须是**可解析的地址**(IP 或真实域名)。nginx 在启动时解析 `proxy_pass` 的主机名,填了不存在的域名会让 nginx 起不来。所以不要填占位符式的假域名。

### 3. 上传音频被 nginx 拒绝(413 Request Entity Too Large)
nginx 默认 `client_max_body_size 1m`。配置里已放宽到 `50m`;若音频更大,改 `nginx/default.conf.template` 里的 `client_max_body_size` 后重新构建。

### 4. 请求超时(504)
LLM 回复可能较慢,nginx 已把 `proxy_read_timeout` 调到 `300s`,与前端 axios 的 `timeout: 120000`(120s)留出余量。若还超时,同步调大两边。

### 5. 刷新子路由 404
前端用 react-router,nginx 已配置 `try_files $uri $uri/ /index.html` 做 SPA 回退,正常不会 404。

### 6. 改了代码/配置后
- 本地:`make dev` 自动热更新。
- Docker:镜像内是构建产物,需 `make docker-up`(带 `--build`)重新构建。
