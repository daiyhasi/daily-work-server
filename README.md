# Daily Work Server

FastAPI 后台，提供训练计划生成接口。

## 启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 接口

- `GET /health`
- `POST /plans/generate`

前端环境变量：

```bash
EXPO_PUBLIC_PLAN_API_URL=http://localhost:8000
```

## Docker

```bash
docker compose up -d --build
docker compose logs -f daily-work-api
```

