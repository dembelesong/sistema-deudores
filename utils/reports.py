"""
Generación de reportes en Excel (.xlsx) para descargar.
"""

import io
import pandas as pd
from datetime import datetime

from utils.queries import (
    list_deudores, totales_deudor, list_productos,
    list_deudas_deudor, list_abonos_deudor,
    list_entradas, list_salidas, list_proveedores,
)
from utils.format import formatear_fecha_hora


def _fecha_ordenable(fecha_iso: str) -> datetime:
    try:
        return datetime.fromisoformat((fecha_iso or "").replace("Z", "+00:00"))
    except Exception:
        return datetime.min


def _guardar_hojas(hojas: dict) -> bytes:
    """hojas = {'NombreHoja': dataframe, ...}"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for nombre_hoja, df in hojas.items():
            hoja = nombre_hoja[:31]
            df.to_excel(writer, index=False, sheet_name=hoja)
            worksheet = writer.sheets[hoja]

            for col_idx, nombre_col in enumerate(df.columns, start=1):
                letra = worksheet.cell(row=1, column=col_idx).column_letter

                # Ancho automático según el contenido más largo de la columna
                largo_max = max(
                    [len(nombre_col)] + [len(str(v)) for v in df[nombre_col].tolist()]
                )
                worksheet.column_dimensions[letra].width = min(largo_max + 3, 40)

                # Teléfono siempre como texto, para que Excel no borre
                # el "+" inicial ni los ceros a la izquierda.
                if "teléfono" in nombre_col.lower():
                    for fila in range(2, len(df) + 2):
                        worksheet.cell(row=fila, column=col_idx).number_format = "@"
    return buffer.getvalue()


def deudores_excel_bytes(supabase) -> bytes:
    """Dos hojas: Resumen (una fila por deudor, con total general) y
    Detalle (una fila por cada deuda/abono individual, con total)."""
    resumen_filas = []
    detalle_filas = []
    total_deuda = total_abonado = total_saldo = 0.0

    for d in list_deudores(supabase):
        deuda, abonado, saldo = totales_deudor(supabase, d["id"])
        resumen_filas.append(
            {
                "Nombre": d["nombre"],
                "Teléfono": d.get("telefono") or "",
                "Deuda": deuda,
                "Abonado": abonado,
                "Saldo": saldo,
            }
        )
        total_deuda += deuda
        total_abonado += abonado
        total_saldo += saldo

        movimientos = []
        for deu in list_deudas_deudor(supabase, d["id"]):
            movimientos.append((_fecha_ordenable(deu["fecha"]), {
                "Deudor": d["nombre"],
                "Tipo": "Deuda",
                "Fecha": formatear_fecha_hora(deu["fecha"]),
                "Descripción": deu.get("descripcion") or "",
                "Monto": float(deu["monto"]),
            }))
        for ab in list_abonos_deudor(supabase, d["id"]):
            movimientos.append((_fecha_ordenable(ab["fecha"]), {
                "Deudor": d["nombre"],
                "Tipo": "Abono",
                "Fecha": formatear_fecha_hora(ab["fecha"]),
                "Descripción": "",
                "Monto": -float(ab["monto"]),
            }))
        movimientos.sort(key=lambda x: x[0])
        detalle_filas.extend(fila for _, fila in movimientos)

    resumen_filas.append(
        {"Nombre": "TOTAL", "Teléfono": "", "Deuda": total_deuda, "Abonado": total_abonado, "Saldo": total_saldo}
    )
    detalle_filas.append(
        {"Deudor": "TOTAL", "Tipo": "", "Fecha": "", "Descripción": "", "Monto": total_saldo}
    )

    df_resumen = pd.DataFrame(resumen_filas, columns=["Nombre", "Teléfono", "Deuda", "Abonado", "Saldo"])
    df_detalle = pd.DataFrame(detalle_filas, columns=["Deudor", "Tipo", "Fecha", "Descripción", "Monto"])

    return _guardar_hojas({"Resumen": df_resumen, "Detalle": df_detalle})


def productos_excel_bytes(supabase) -> bytes:
    filas = []
    total_stock = 0.0
    total_valor = 0.0
    for p in list_productos(supabase):
        proveedor_nombre = (p.get("proveedores") or {}).get("nombre", "")
        stock = float(p["stock"])
        precio_venta = float(p.get("precio_venta") or 0)
        valor_total = stock * precio_venta
        total_stock += stock
        total_valor += valor_total
        filas.append(
            {
                "Nombre": p["nombre"],
                "Categoría": p.get("categoria") or "",
                "Stock": p["stock"],
                "Stock mínimo": p.get("stock_minimo") or 0,
                "Precio compra": p.get("precio_compra") or 0,
                "Precio venta": p.get("precio_venta") or 0,
                "Valor total (venta)": valor_total,
                "Proveedor": proveedor_nombre,
            }
        )
    filas.append(
        {
            "Nombre": "TOTAL", "Categoría": "", "Stock": total_stock, "Stock mínimo": "",
            "Precio compra": "", "Precio venta": "", "Valor total (venta)": total_valor, "Proveedor": "",
        }
    )
    df = pd.DataFrame(
        filas,
        columns=["Nombre", "Categoría", "Stock", "Stock mínimo", "Precio compra", "Precio venta", "Valor total (venta)", "Proveedor"],
    )
    return _guardar_hojas({"Productos": df})


def entradas_excel_bytes(supabase) -> bytes:
    filas = []
    total = 0.0
    for e in list_entradas(supabase):
        nombre_producto = (e.get("productos") or {}).get("nombre", "")
        nombre_proveedor = (e.get("proveedores") or {}).get("nombre", "")
        monto = float(e["cantidad"]) * float(e.get("precio_unitario") or 0)
        total += monto
        filas.append(
            {
                "Fecha": formatear_fecha_hora(e["fecha"]),
                "Producto": nombre_producto,
                "Cantidad": e["cantidad"],
                "Precio unitario": e.get("precio_unitario") or 0,
                "Total": monto,
                "Proveedor": nombre_proveedor,
                "Notas": e.get("notas") or "",
            }
        )
    filas.append({"Fecha": "", "Producto": "TOTAL", "Cantidad": "", "Precio unitario": "", "Total": total, "Proveedor": "", "Notas": ""})
    df = pd.DataFrame(filas, columns=["Fecha", "Producto", "Cantidad", "Precio unitario", "Total", "Proveedor", "Notas"])
    return _guardar_hojas({"Entradas": df})


def salidas_excel_bytes(supabase) -> bytes:
    filas = []
    total = 0.0
    for s in list_salidas(supabase):
        nombre_producto = (s.get("productos") or {}).get("nombre", "")
        monto = float(s["cantidad"]) * float(s.get("precio_unitario") or 0)
        total += monto
        filas.append(
            {
                "Fecha": formatear_fecha_hora(s["fecha"]),
                "Producto": nombre_producto,
                "Cantidad": s["cantidad"],
                "Precio unitario": s.get("precio_unitario") or 0,
                "Total": monto,
                "Notas": s.get("notas") or "",
            }
        )
    filas.append({"Fecha": "", "Producto": "TOTAL", "Cantidad": "", "Precio unitario": "", "Total": total, "Notas": ""})
    df = pd.DataFrame(filas, columns=["Fecha", "Producto", "Cantidad", "Precio unitario", "Total", "Notas"])
    return _guardar_hojas({"Salidas": df})


def proveedores_excel_bytes(supabase) -> bytes:
    filas = []
    for p in list_proveedores(supabase):
        filas.append(
            {
                "Nombre": p["nombre"],
                "Teléfono": p.get("telefono") or "",
                "Correo": p.get("email") or "",
                "Notas": p.get("notas") or "",
            }
        )
    df = pd.DataFrame(filas, columns=["Nombre", "Teléfono", "Correo", "Notas"])
    return _guardar_hojas({"Proveedores": df})
