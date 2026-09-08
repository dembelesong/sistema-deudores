"""
Formateo de fechas: Supabase guarda todo en UTC, así que convertimos a
la hora de Chile antes de mostrarla.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

CHILE_TZ = ZoneInfo("America/Santiago")


def formatear_fecha_hora(fecha_iso: str) -> str:
    """'2026-09-02T17:00:00+00:00' -> '02-09-2026 17:00' (hora de Chile)."""
    if not fecha_iso:
        return ""
    try:
        texto = fecha_iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(texto)
        dt_local = dt.astimezone(CHILE_TZ)
        return dt_local.strftime("%d-%m-%Y %H:%M")
    except Exception:
        return fecha_iso[:10]


def dias_desde(fecha_iso: str) -> int:
    """Cuántos días completos han pasado desde esa fecha hasta ahora."""
    try:
        texto = fecha_iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(texto)
        ahora = datetime.now(timezone.utc)
        return max((ahora - dt).days, 0)
    except Exception:
        return 0
