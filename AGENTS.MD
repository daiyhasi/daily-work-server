# Daily Work Server Notes

## 项目

- 当前目录：`/Users/daiyhasi/Desktop/demo/daily-work-server`
- 服务：Python FastAPI
- 接口：`POST /plans/generate`
- 前端目录：`/Users/daiyhasi/Desktop/demo/daily-work`

## 本地启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

前端连接：

```bash
EXPO_PUBLIC_PLAN_API_URL=http://localhost:8000
```

## 服务器

- 公网 IP：`121.41.23.136`
- SSH 用户：`root`
- 登录密钥：`key-blog.pem`
- 建议部署目录：`/opt/daily-work-server`

登录：

```bash
ssh -i key-blog.pem root@121.41.23.136
```

部署：

```bash
cd /opt/daily-work-server
docker compose up -d --build
```

查看：

```bash
docker compose ps
docker compose logs -f daily-work-api
```

## 环境变量

服务器和本地都使用 `.env`，不要提交：

```bash
OPENAI_API_KEY=你的密钥
OPENAI_BASE_URL=http://cloud.omnimind.com.cn/v1
OPENAI_MODEL=gpt-5.5
PORT=8000
```

## 注意

- 不要提交 `.env`、`.venv/`、`*.pem`。
- 不要在文档、日志或回复里输出私钥内容。
- 后端改动后至少跑：`.venv/bin/pytest -q`。

