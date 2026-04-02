#!/usr/bin/env python3
"""server.py — ZipPasswordCrack.in v46 ULTRA"""
import os, sys, multiprocessing

# CRITICAL: set 'fork' before any imports — needed for Process() inside waitress
try:
    multiprocessing.set_start_method("fork", force=True)
except RuntimeError:
    pass

_raw = os.environ.get("PORT", "8080")
try:
    PORT = int(_raw)
    if not (1 <= PORT <= 65535): PORT = 8080
except Exception:
    PORT = 8080

print(f"[server.py] PORT={PORT}", flush=True)

from crackpro import app

try:
    from waitress import serve
    print(f"[server.py] Starting waitress on 0.0.0.0:{PORT}", flush=True)
    serve(app, host="0.0.0.0", port=PORT, threads=32, connection_limit=2000,
          channel_timeout=900, max_request_body_size=209715200, ident="ZipCrack")
except ImportError:
    try:
        from gunicorn.app.base import BaseApplication
        class _G(BaseApplication):
            def __init__(self, app, opts=None):
                self.options=opts or {}; self.application=app; super().__init__()
            def load_config(self):
                for k,v in self.options.items():
                    if k in self.cfg.settings: self.cfg.set(k.lower(),v)
            def load(self): return self.application
        print(f"[server.py] Starting gunicorn on 0.0.0.0:{PORT}", flush=True)
        _G(app, {"bind":f"0.0.0.0:{PORT}","workers":1,"threads":16,
                  "worker_class":"gthread","timeout":900,"loglevel":"info",
                  "accesslog":"-","errorlog":"-"}).run()
    except Exception:
        print(f"[server.py] Flask fallback on port {PORT}", flush=True)
        app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True, use_reloader=False)
