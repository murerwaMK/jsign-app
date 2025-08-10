from jsign import create_app
from cloudflare import ASGI

app = create_app()

def fetch(request):
    return ASGI(app).fetch(request)