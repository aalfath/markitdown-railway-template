"""MarkItDown as a small authenticated service.

POST /convert  multipart file upload (field "file") or JSON {"uri": "https://..."} -> Markdown
/mcp           MCP Streamable HTTP endpoint with the convert_to_markdown tool
GET /healthz   unauthenticated health check

Every other request needs "Authorization: Bearer $MARKITDOWN_API_TOKEN".
Only http:, https: and data: URIs are accepted, so the service never reads its own files.
"""
import contextlib
import hmac
import os
import tempfile
from urllib.parse import urlparse

import anyio
import uvicorn
from markitdown import FileConversionException, MarkItDown, UnsupportedFormatException
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route

TOKEN = os.environ.get("MARKITDOWN_API_TOKEN", "")
MAX_UPLOAD = int(os.environ.get("MARKITDOWN_MAX_UPLOAD_MB", "50")) * 1024 * 1024
ENABLE_PLUGINS = os.environ.get("MARKITDOWN_ENABLE_PLUGINS", "false").lower() in ("1", "true", "yes")
ALLOWED_SCHEMES = {"http", "https", "data"}

if len(TOKEN) < 16:
    raise SystemExit("MARKITDOWN_API_TOKEN must be set (at least 16 characters)")


def converter() -> MarkItDown:
    return MarkItDown(enable_plugins=ENABLE_PLUGINS)


def convert_uri(uri: str):
    if urlparse(uri).scheme.lower() not in ALLOWED_SCHEMES:
        raise ValueError("Only http:, https: and data: URIs are allowed")
    return converter().convert_uri(uri)


mcp = MCPServer("markitdown")


@mcp.tool()
async def convert_to_markdown(uri: str) -> str:
    """Convert a document at an http:, https: or data: URI (PDF, Word, Excel, PowerPoint, HTML, images, ...) to Markdown."""
    try:
        return (await anyio.to_thread.run_sync(convert_uri, uri)).markdown
    except (ValueError, UnsupportedFormatException, FileConversionException) as exc:
        raise ToolError(str(exc)) from exc
    except Exception as exc:  # network errors and similar
        raise ToolError(f"Could not convert the resource: {exc.__class__.__name__}") from exc


async def convert(request: Request):
    try:
        if request.headers.get("content-type", "").startswith("multipart/form-data"):
            form = await request.form(max_part_size=MAX_UPLOAD)
            upload = form.get("file")
            if upload is None or not hasattr(upload, "read"):
                return JSONResponse({"error": "multipart field 'file' is required"}, 400)
            suffix = os.path.splitext(upload.filename or "")[1]
            with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
                tmp.write(await upload.read())
                tmp.flush()
                result = await anyio.to_thread.run_sync(converter().convert, tmp.name)
        else:
            body = await request.json()
            result = await anyio.to_thread.run_sync(convert_uri, str(body.get("uri", "")))
    except (ValueError, UnsupportedFormatException, FileConversionException) as exc:
        return JSONResponse({"error": str(exc)}, 400)
    except Exception as exc:
        return JSONResponse({"error": f"Could not convert: {exc.__class__.__name__}"}, 502)
    if request.query_params.get("format") == "text":
        return PlainTextResponse(result.markdown, media_type="text/markdown")
    return JSONResponse({"title": result.title, "markdown": result.markdown})


async def healthz(request: Request):
    return PlainTextResponse("ok")


class BearerAuth:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] != "/healthz":
            headers = dict(scope["headers"])
            given = headers.get(b"authorization", b"").decode()
            if not hmac.compare_digest(given, f"Bearer {TOKEN}"):
                await PlainTextResponse("Unauthorized", 401)(scope, receive, send)
                return
        await self.app(scope, receive, send)


http_app = mcp.streamable_http_app(json_response=True, stateless_http=True, host="0.0.0.0")


@contextlib.asynccontextmanager
async def lifespan(app):
    async with http_app.router.lifespan_context(app):
        yield


app = Starlette(
    routes=[Route("/healthz", healthz), Route("/convert", convert, methods=["POST"]), *http_app.routes],
    lifespan=lifespan,
)

if __name__ == "__main__":
    # "" binds every IPv4 and IPv6 address (uvicorn treats "::" as IPv6-only).
    uvicorn.run(BearerAuth(app), host=os.environ.get("HOST", ""), port=int(os.environ.get("PORT", "8080")),
                proxy_headers=True, forwarded_allow_ips="*")
