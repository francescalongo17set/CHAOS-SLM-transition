"""Shared retrieval server: loads the embedding model ONCE and answers retrieve() calls from many processes/agents.
Start (background):  python -I code/retrieval_server.py      Stop: kill the process or Ctrl-C.
Listens on 127.0.0.1 only (port 8765, env RETRIEVE_PORT). Same results as local retrieve() (it calls it)."""
import json, os, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
os.environ["RETRIEVE_NO_SERVER"] = "1"          # the server itself must compute locally
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import retrieve as R
try:
    import torch; torch.set_num_threads(int(os.environ.get("RETRIEVE_THREADS", "4")))
except Exception: pass
LOCK = threading.Lock()                          # one encode at a time: bounded memory and CPU

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            q = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            with LOCK: out = R.retrieve(q["question"], q["doc_id"], q.get("k", 5), q.get("model"))
            body = json.dumps(out, ensure_ascii=False).encode(); self.send_response(200)
        except Exception as e:
            body = json.dumps({"error": str(e)}).encode(); self.send_response(500)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass

if __name__ == "__main__":
    active = json.load(open(R.IDX / "retrieval_config.json"))["active"]
    R._load(active)                              # load now so the first request is fast
    print(f"retrieval server ready on 127.0.0.1:{R.PORT} (model {active})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", R.PORT), H).serve_forever()
