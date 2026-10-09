# Home Services Agent

Agent LangGraph tìm dịch vụ gia đình, dùng Gemini và MongoDB Atlas.

## Chạy
```bash
cp .env.example .env     # điền key Gemini và URI Atlas
docker compose run --rm app
```

## Test
```bash
docker compose --profile test run --rm test
```