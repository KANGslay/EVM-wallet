from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.api import auth, wallet, ai

app = FastAPI(
    title=settings.APP_NAME,
    description="EVM托管钱包系统API",
    version="1.0.0"
)

# 配置CORS
# 添加必要的源到允许列表中
origins = settings.CORS_ORIGINS.copy()
if 'null' not in origins:
    origins.append('null')
if 'http://localhost:8081' not in origins:
    origins.append('http://localhost:8081')
if 'http://localhost' not in origins:
    origins.append('http://localhost')

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 使用扩展后的CORS_ORIGINS
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],  # 明确指定允许的HTTP方法
    allow_headers=[
        "*",
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],  # 明确指定允许的请求头
    expose_headers=[
        "Content-Length",
        "X-Total-Count",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Credentials"
    ],  # 明确指定暴露的响应头
    max_age=3600,  # 预检请求的缓存时间（1小时）
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(wallet.router, prefix="/api/wallet", tags=["钱包"])  # 修改为固定前缀
app.include_router(ai.router, prefix="/api/ai", tags=["AI对话"])  # 修改为固定前缀

@app.get("/")
async def root():
    return {"message": "欢迎使用EVM托管钱包系统"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
    
# 独立运行时的入口点
if __name__ == "__main__":
    # 在8080端口运行，与MCP配置文件中的端口保持一致
    uvicorn.run(app, host="0.0.0.0", port=8080)