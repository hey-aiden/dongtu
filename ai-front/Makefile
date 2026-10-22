.PHONY: dev install build docker-build docker-up docker-down

dev:            ## 本地开发:起 dev server(热更新)
	pnpm start

install:        ## 安装依赖(首次 / 依赖变更后)
	pnpm install

build:          ## 本地构建生产产物到 build/
	pnpm build

docker-build:   ## 构建线上镜像
	docker build -t ai-front:latest .

docker-up:      ## 起线上容器(含重新构建)
	docker-compose up -d --build

docker-down:    ## 停掉线上容器
	docker-compose down
