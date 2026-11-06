"""Zählt im Betrieb pro View: Requests, CPU-Zeit (Django-Thread und PostgreSQL-Backend), Antwortgröße.

Speichert nur Summen je View, keine Nutzer-IDs, keine IP-Adressen. Schreibt alle 5 Minuten eine JSON-Zeile je View.
"""

import atexit
import json
import threading
import time
from collections import defaultdict
from datetime import datetime

from django.conf import settings

from carbon.cpu import DbCpuMeter

FLUSH_SECONDS = 300


class EnergyMeterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.local = threading.local()
        self.lock = threading.Lock()
        self.stats = defaultdict(lambda: {"requests": 0, "python_cpu_ns": 0, "db_cpu_ns": 0, "bytes": 0})
        self.last_flush = time.monotonic()
        self.path = settings.LOGS_DIR / "energy_usage.jsonl"
        atexit.register(self.flush)

    def _meter(self):
        if not hasattr(self.local, "meter"):
            self.local.meter = DbCpuMeter()
        return self.local.meter

    def __call__(self, request):
        meter = self._meter()
        meter.attach()
        py0, db0 = time.thread_time_ns(), meter.read_ns()
        response = self.get_response(request)
        py = time.thread_time_ns() - py0
        db = meter.read_ns() - db0

        match = getattr(request, "resolver_match", None)
        view = match.view_name if match else "unresolved"
        with self.lock:
            entry = self.stats[(view, request.method)]
            entry["requests"] += 1
            entry["python_cpu_ns"] += py
            entry["db_cpu_ns"] += db
            entry["bytes"] += len(getattr(response, "content", b""))
        if time.monotonic() - self.last_flush > FLUSH_SECONDS:
            self.flush()
        return response

    def flush(self):
        with self.lock:
            if not self.stats:
                return
            now = datetime.now().isoformat(timespec="seconds")
            lines = [json.dumps({"ts": now, "view": v, "method": m, **s}) for (v, m), s in self.stats.items()]
            self.stats.clear()
            self.last_flush = time.monotonic()
        with open(self.path, "a") as fh:
            fh.write("\n".join(lines) + "\n")
