from jsign import create_app
from cloudflare import ASGI

app = create_app()

async def fetch(request):
    return await ASGI(app)(request)