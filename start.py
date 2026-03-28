#!/usr/bin/env python3
"""start.py v37 — ZipPasswordCrack.in — Railway PORT fix"""
import os, sys

def get_port():
    raw = os.environ.get("PORT", "8080")
    try:
        p = int(str(raw).strip())
        if 1 <= p <= 65535:
            return p
    except (ValueError, TypeError):
        pass
    print(f"[start.py] PORT='{raw}' invalid → using 8080", flush=True)
    return 8080

port = get_port()
print(f"[start.py] Binding on port {port}", flush=True)

cmd = [
    sys.executable, "-m", "gunicorn",
    "--workers", "2",
    "--threads", "8",
    "--worker-class", "gthread",
    "--timeout", "300",
    "--keep-alive", "30",
    "--max-requests", "1000",
    "--max-requests-jitter", "100",
    "--graceful-timeout", "60",
    "--log-level", "info",
    "--access-logfile", "-",
    "--error-logfile", "-",
    "--bind", f"0.0.0.0:{port}",
    "crackpro:app"
]
os.execv(sys.executable, cmd)
