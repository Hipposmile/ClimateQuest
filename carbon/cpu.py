"""CPU-Zeit-Messung: Django-Prozess plus das PostgreSQL-Backend, das die Abfragen dieser Verbindung ausführt."""

import time
from pathlib import Path

import psutil
from django.db import connection


class DbCpuMeter:
    """Liest die bisher verbrauchte CPU-Zeit des PostgreSQL-Backends der aktuellen Django-Verbindung (in ns).

    Bei SQLite läuft die Datenbank im Django-Prozess, dort ist die Zeit schon in ``process_time`` enthalten.
    """

    def __init__(self):
        self.pid = None
        self.source = "none"  # "schedstat", "psutil" oder "none"

    def attach(self):
        """Verbindung öffnen und die Prozess-ID des zugehörigen PostgreSQL-Backends merken."""
        if connection.vendor != "postgresql":
            self.pid, self.source = None, "none"
            return
        connection.ensure_connection()
        pid = connection.connection.get_backend_pid()  # psycopg2
        if pid != self.pid:
            self.pid = pid
            self.source = "schedstat" if self._schedstat_ns() else "psutil"

    def _schedstat_ns(self):
        try:
            # Erstes Feld: Zeit auf der CPU in Nanosekunden. Fehlt die Datei oder steht 0 drin, ist sie nicht nutzbar.
            return int(Path(f"/proc/{self.pid}/schedstat").read_text().split()[0])
        except (OSError, ValueError, IndexError):
            return 0

    def read_ns(self):
        if self.pid is None:
            return 0
        if self.source == "schedstat":
            return self._schedstat_ns()
        cpu = psutil.Process(self.pid).cpu_times()  # Auflösung nur 10 ms: erst über viele Wiederholungen aussagekräftig
        return int((cpu.user + cpu.system) * 1e9)


class CpuMeasurement:
    """Kontextmanager: misst Wandzeit, Python-CPU-Zeit und Datenbank-CPU-Zeit eines Blocks."""

    def __init__(self, db_meter):
        self.db = db_meter

    def __enter__(self):
        self.db.attach()
        self._wall = time.perf_counter_ns()
        self._py = time.process_time_ns()
        self._db = self.db.read_ns()
        return self

    def __exit__(self, *exc):
        self.db_cpu_ns = self.db.read_ns() - self._db
        self.python_cpu_ns = time.process_time_ns() - self._py
        self.wall_ns = time.perf_counter_ns() - self._wall
        return False

    @property
    def cpu_s(self):
        return (self.python_cpu_ns + self.db_cpu_ns) / 1e9
