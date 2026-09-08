"""
Funciones de acceso a datos. Todas asumen que el cliente de Supabase
ya está autenticado (sesión del usuario), por lo que RLS filtra
automáticamente las filas de cada usuario.

Las funciones de lectura (list_*, totales_*) devuelven un valor por
defecto seguro (lista vacía, ceros) si algo falla en vez de romper la
página. Las funciones que escriben (add_*, update_*, delete_*) devuelven
True si funcionó y False si falló, para que la página pueda decidir si
mostrar éxito o no.
"""

from utils.auth import current_user_id, current_negocio_id
from utils.errors import db_safe
from utils.format import dias_desde


# ---------- Proveedores ----------

@db_safe(default=[])
def list_proveedores(supabase):
    return supabase.table("proveedores").select("*").order("nombre").execute().data


@db_safe(default=False)
def add_proveedor(supabase, nombre, telefono, email, notas):
    supabase.table("proveedores").insert(
        {
            "user_id": current_user_id(),
            "negocio_id": current_negocio_id(),
            "nombre": nombre,
            "telefono": telefono,
            "email": email,
            "notas": notas,
        }
    ).execute()
    return True


@db_safe(default=False)
def update_proveedor(supabase, proveedor_id, nombre, telefono, email, notas):
    supabase.table("proveedores").update(
        {"nombre": nombre, "telefono": telefono, "email": email, "notas": notas}
    ).eq("id", proveedor_id).execute()
    return True


@db_safe(default=False)
def delete_proveedor(supabase, proveedor_id):
    supabase.table("proveedores").delete().eq("id", proveedor_id).execute()
    return True


# ---------- Productos ----------

@db_safe(default=[])
def list_productos(supabase):
    return (
        supabase.table("productos")
        .select("*, proveedores(nombre)")
        .order("nombre")
        .execute()
        .data
    )


@db_safe(default=[])
def productos_bajo_stock(supabase):
    productos = list_productos(supabase)
    return [
        p for p in productos
        if float(p.get("stock") or 0) <= float(p.get("stock_minimo") or 0)
    ]


@db_safe(default=False)
def add_producto(supabase, nombre, categoria, stock, stock_minimo, precio_compra, precio_venta, proveedor_id):
    supabase.table("productos").insert(
        {
            "user_id": current_user_id(),
            "negocio_id": current_negocio_id(),
            "nombre": nombre,
            "categoria": categoria,
            "stock": stock,
            "stock_minimo": stock_minimo,
            "precio_compra": precio_compra,
            "precio_venta": precio_venta,
            "proveedor_id": proveedor_id,
        }
    ).execute()
    return True


@db_safe(default=False)
def update_producto(supabase, producto_id, nombre, categoria, stock, stock_minimo, precio_compra, precio_venta, proveedor_id):
    supabase.table("productos").update(
        {
            "nombre": nombre,
            "categoria": categoria,
            "stock": stock,
            "stock_minimo": stock_minimo,
            "precio_compra": precio_compra,
            "precio_venta": precio_venta,
            "proveedor_id": proveedor_id,
        }
    ).eq("id", producto_id).execute()
    return True


@db_safe(default=False)
def delete_producto(supabase, producto_id):
    supabase.table("productos").delete().eq("id", producto_id).execute()
    return True


def _adjust_stock(supabase, producto_id, delta):
    row = supabase.table("productos").select("stock").eq("id", producto_id).single().execute().data
    nuevo_stock = float(row["stock"]) + delta
    supabase.table("productos").update({"stock": nuevo_stock}).eq("id", producto_id).execute()


# ---------- Entradas ----------

@db_safe(default=[])
def list_entradas(supabase):
    return (
        supabase.table("entradas")
        .select("*, productos(nombre), proveedores(nombre)")
        .order("fecha", desc=True)
        .execute()
        .data
    )


@db_safe(default=False)
def add_entrada(supabase, producto_id, cantidad, precio_unitario, proveedor_id, notas):
    supabase.table("entradas").insert(
        {
            "user_id": current_user_id(),
            "negocio_id": current_negocio_id(),
            "producto_id": producto_id,
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "proveedor_id": proveedor_id,
            "notas": notas,
        }
    ).execute()
    _adjust_stock(supabase, producto_id, cantidad)
    return True


# ---------- Salidas ----------

@db_safe(default=[])
def list_salidas(supabase):
    return (
        supabase.table("salidas")
        .select("*, productos(nombre)")
        .order("fecha", desc=True)
        .execute()
        .data
    )


@db_safe(default=False)
def add_salida(supabase, producto_id, cantidad, precio_unitario, notas):
    supabase.table("salidas").insert(
        {
            "user_id": current_user_id(),
            "negocio_id": current_negocio_id(),
            "producto_id": producto_id,
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "notas": notas,
        }
    ).execute()
    _adjust_stock(supabase, producto_id, -cantidad)
    return True


# ---------- Deudores ----------

@db_safe(default=[])
def list_deudores(supabase):
    return supabase.table("deudores").select("*").order("nombre").execute().data


@db_safe(default=None)
def add_deudor(supabase, nombre, telefono, notas):
    res = supabase.table("deudores").insert(
        {
            "user_id": current_user_id(),
            "negocio_id": current_negocio_id(),
            "nombre": nombre,
            "telefono": telefono,
            "notas": notas,
        }
    ).execute()
    return res.data[0]["id"] if res.data else None


@db_safe(default=False)
def update_deudor(supabase, deudor_id, nombre, telefono, notas):
    supabase.table("deudores").update(
        {"nombre": nombre, "telefono": telefono, "notas": notas}
    ).eq("id", deudor_id).execute()
    return True


@db_safe(default=False)
def delete_deudor(supabase, deudor_id):
    supabase.table("deudores").delete().eq("id", deudor_id).execute()
    return True


@db_safe(default=False)
def add_deuda(supabase, deudor_id, monto, descripcion):
    supabase.table("deudas").insert(
        {
            "user_id": current_user_id(),
            "negocio_id": current_negocio_id(),
            "deudor_id": deudor_id,
            "monto": monto,
            "descripcion": descripcion,
        }
    ).execute()
    return True


@db_safe(default=False)
def delete_deuda(supabase, deuda_id):
    supabase.table("deudas").delete().eq("id", deuda_id).execute()
    return True


@db_safe(default=False)
def add_abono(supabase, deudor_id, monto):
    supabase.table("abonos").insert(
        {
            "user_id": current_user_id(),
            "negocio_id": current_negocio_id(),
            "deudor_id": deudor_id,
            "monto": monto,
        }
    ).execute()
    return True


@db_safe(default=False)
def delete_abono(supabase, abono_id):
    supabase.table("abonos").delete().eq("id", abono_id).execute()
    return True


@db_safe(default=[])
def list_deudas_deudor(supabase, deudor_id):
    return (
        supabase.table("deudas")
        .select("*")
        .eq("deudor_id", deudor_id)
        .order("fecha", desc=True)
        .execute()
        .data
    )


@db_safe(default=[])
def list_abonos_deudor(supabase, deudor_id):
    return (
        supabase.table("abonos")
        .select("*")
        .eq("deudor_id", deudor_id)
        .order("fecha", desc=True)
        .execute()
        .data
    )


@db_safe(default=(0.0, 0.0, 0.0))
def totales_deudor(supabase, deudor_id):
    deudas = supabase.table("deudas").select("monto").eq("deudor_id", deudor_id).execute().data
    abonos = supabase.table("abonos").select("monto").eq("deudor_id", deudor_id).execute().data
    total_deuda = sum(float(d["monto"]) for d in deudas)
    total_abonado = sum(float(a["monto"]) for a in abonos)
    return total_deuda, total_abonado, total_deuda - total_abonado


@db_safe(default=0.0)
def total_por_cobrar(supabase):
    deudores = list_deudores(supabase)
    total = 0.0
    for d in deudores:
        _, _, saldo = totales_deudor(supabase, d["id"])
        total += saldo
    return total


@db_safe(default=None)
def dias_atraso_deudor(supabase, deudor_id):
    """Días desde la deuda más antigua sin pagar (None si está al día)."""
    _, _, saldo = totales_deudor(supabase, deudor_id)
    if saldo <= 0:
        return None
    deudas = list_deudas_deudor(supabase, deudor_id)
    if not deudas:
        return None
    return max(dias_desde(d["fecha"]) for d in deudas)
