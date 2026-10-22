# 构建阶段:用 pnpm 编译 CRA 静态产物
# pnpm 11 需要 Node >= 22.13,与本机 Node 24 对齐
FROM node:24-alpine AS build
RUN npm install -g pnpm@11.18.0
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

# 运行阶段:用 nginx 托管静态文件 + 反向代理后端
FROM nginx:1.27-alpine
# 模板里的 ${BACKEND_URL} 会在容器启动时由 nginx 镜像的 envsubst 机制替换
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
