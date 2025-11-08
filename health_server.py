# health_server.py
from aiohttp import web
import asyncio

async def health_check(request):
    return web.Response(text="Bot is alive")

async def start_health_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("✅ Health server started on port 8080")

if __name__ == "__main__":
    asyncio.run(start_health_server())