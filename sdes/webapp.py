"""仅监听回环地址的本地 GUI 服务；运行不依赖第三方库。"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser
from .core import parse_bits, trace_block
from .experiments import encode_text, decode_text, crack_keys, collision_report

ROOT = Path(__file__).resolve().parent.parent


def dispatch(payload: dict) -> dict:
    action = payload.get("action")
    if action in ("encrypt", "decrypt"):
        return trace_block(parse_bits(payload["block"], 8, "分组"),
                           parse_bits(payload["key"], 10, "密钥"), action == "decrypt")
    if action in ("encode", "decode"):
        key = parse_bits(payload["key"], 10, "密钥")
        method = encode_text if action == "encode" else decode_text
        return method(payload["text"], key, payload.get("encoding", "ascii"))
    if action == "crack":
        rows = [line.split() for line in payload["pairs"].splitlines() if line.strip()]
        if len(rows) > 256 or any(len(row) != 2 for row in rows):
            raise ValueError("每行填写两个 8 位二进制数：明文 空格 密文；最多 256 行")
        return crack_keys([(parse_bits(p, 8, "明文"), parse_bits(c, 8, "密文")) for p, c in rows])
    if action == "collisions":
        return collision_report(parse_bits(payload["block"], 8, "明文"))
    raise ValueError("未知操作")


class Handler(BaseHTTPRequestHandler):
    def send_data(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        files = {"/": ("web/index.html", "text/html; charset=utf-8"),
                 "/app.js": ("web/app.js", "text/javascript; charset=utf-8"),
                 "/style.css": ("web/style.css", "text/css; charset=utf-8")}
        if self.path not in files:
            self.send_data(404, b"Not found", "text/plain")
            return
        path, mime = files[self.path]
        self.send_data(200, (ROOT / path).read_bytes(), mime)

    def do_POST(self):
        if self.path != "/api":
            self.send_data(404, b"Not found", "text/plain")
            return
        # 禁止其他网站跨源调用本地服务，限制输入体积。
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{self.headers.get('Host')}":
            self.send_data(403, b"Cross-origin request rejected", "text/plain")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65536:
                raise ValueError("输入体积必须在 1 到 65536 字节之间")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("请求必须是 JSON 对象")
            response, status = dispatch(payload), 200
        except (ValueError, KeyError, TypeError, UnicodeError) as error:
            response, status = {"error": str(error)}, 400
        self.send_data(status, json.dumps(response, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")


def main():
    parser = argparse.ArgumentParser(description="S-DES 本地实验 GUI")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    address = f"http://127.0.0.1:{args.port}"
    print(f"S-DES 实验台：{address}（Ctrl+C 结束）", flush=True)
    if args.open:
        webbrowser.open(address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
