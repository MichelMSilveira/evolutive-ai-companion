"""Read-only local PC audit for Nova's assistant mode."""
from __future__ import annotations

import platform
import socket
from datetime import datetime, timezone

import psutil


def snapshot() -> dict:
    """Collect safe diagnostics without reading private files or changing state."""
    memory = psutil.virtual_memory()
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({"mount": part.mountpoint, "percent": usage.percent, "free_gb": round(usage.free / 2**30, 1)})
        except OSError:
            continue
    processes = []
    for process in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
        try:
            info = process.info
            processes.append({"name": info.get("name"), "cpu_percent": round(info.get("cpu_percent") or 0, 1), "memory_percent": round(info.get("memory_percent") or 0, 1)})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    processes.sort(key=lambda item: item["memory_percent"], reverse=True)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": socket.gethostname(),
        "system": platform.platform(),
        "cpu_percent": psutil.cpu_percent(interval=0.25),
        "memory_percent": memory.percent,
        "memory_available_gb": round(memory.available / 2**30, 1),
        "disks": disks,
        "top_processes": processes[:12],
        "privacy": {"read_only": True, "files_read": False, "screen_capture": False, "network_scan": False},
    }


def summary() -> str:
    data = snapshot()
    return (f"Auditoria local: CPU {data['cpu_percent']:.0f}%, memória {data['memory_percent']:.0f}% "
            f"({data['memory_available_gb']:.1f} GB disponíveis). "
            f"Foram encontrados {len(data['top_processes'])} processos principais. "
            "Modo somente leitura; nenhum arquivo ou tela foi acessado.")
