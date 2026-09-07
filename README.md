# 📦 HVM — Inventario y Fiados

Sistema con Python + Streamlit + Supabase para llevar:
- **Panel**: resumen general, alertas de stock bajo y gráficos de ventas.
- **Productos**: catálogo e inventario, con edición y stock mínimo.
- **Entradas**: ingreso de mercadería (suma stock).
- **Salidas**: ventas/egresos (resta stock).
- **Proveedores**: a quién le compras, con edición.
- **Deudores**: fiados — deuda, abonado, saldo, historial detallado,
  recordatorio por WhatsApp y exportación a Excel.

Incluye login con correo y contraseña (Supabase Auth), recuperación de
contraseña olvidada, y búsqueda en todas las listas. Cada usuario ve
únicamente sus propios datos.

---

## Si ya tenías el sistema instalado antes (actualización)

Si venías de una versión anterior, hay dos cosas que debes hacer una sola vez:

1. **Vuelve a correr `supabase_schema.sql`** completo en el SQL Editor de
   Supabase. Es seguro hacerlo de nuevo: no borra tus datos, solo agrega
   la columna nueva `stock_minimo` que faltaba.
2. **Habilita la recuperación de contraseña**: ve a tu proyecto de Supabase
   → **Authentication → URL Configuration**, y en "Redirect URLs" agrega
   la dirección donde corre tu app, por ejemplo:
   - `http://localhost:8501` (para cuando la uses en tu computador)
   - `https://tu-app.streamlit.app` (para cuando la uses desde internet)

   Sin este paso, el enlace de "olvidé mi contraseña" no va a saber a
   dónde llevar al usuario de vuelta.

---

## 1. Crear el proyecto en Supabase (una sola vez)

1. Ve a https://supabase.com y crea una cuenta gratis (o inicia sesión).
2. Clic en **New Project**. Elige nombre, contraseña de base de datos y región
   (elige una cercana, ej. South America si está disponible).
3. Cuando el proyecto termine de crearse, ve a **Project Settings → API**.
   Ahí vas a encontrar dos datos que necesitas:
   - **Project URL** → esto es tu `SUPABASE_URL`
   - **anon public key** → esto es tu `SUPABASE_KEY`
   (⚠️ usa la llave `anon public`, **no** la `service_role`).
4. Ve a **SQL Editor → New query**, pega todo el contenido del archivo
   `supabase_schema.sql` (incluido en este proyecto) y presiona **Run**.
   Esto crea las tablas y las reglas de seguridad (RLS).
5. (Opcional pero recomendado para pruebas rápidas) Ve a
   **Authentication → Providers → Email** y desactiva "Confirm email" si no
   quieres que cada cuenta nueva tenga que confirmar por correo antes de
   poder entrar.

---

## 2. Correr el sistema en tu computador (local)

Requisitos: tener Python 3.10+ instalado.

```bash
# 1. Entra a la carpeta del proyecto
cd sistema_deudores

# 2. (Recomendado) crea un entorno virtual
python -m venv .venv
source .venv/bin/activate      # En Windows: .venv\Scripts\activate

# 3. Instala las dependencias
pip install -r requirements.txt

# 4. Configura tus credenciales
cp .env.example .env
# Abre .env y reemplaza SUPABASE_URL y SUPABASE_KEY con tus datos reales

# 5. Ejecuta la app
streamlit run app.py
```

Se abrirá automáticamente en tu navegador en `http://localhost:8501`.
La primera vez, usa la pestaña **Crear cuenta** para registrar tu usuario.

---

## 3. Publicarlo en internet (Streamlit Community Cloud, gratis)

1. Sube esta carpeta a un repositorio de GitHub (puede ser privado).
2. Ve a https://share.streamlit.io y conéctalo con tu cuenta de GitHub.
3. Clic en **New app**, elige el repositorio y como archivo principal
   selecciona `app.py`.
4. Antes de darle "Deploy", entra a **Advanced settings → Secrets** y pega
   el contenido de `.streamlit/secrets.toml.example` reemplazando los
   valores por tus credenciales reales:
   ```toml
   SUPABASE_URL = "https://tu-proyecto.supabase.co"
   SUPABASE_KEY = "tu_anon_key_publica"
   ```
5. Dale **Deploy**. En unos minutos tu app queda disponible en una URL
   pública (algo como `tu-app.streamlit.app`), sin tocar nada de código.

**Nota:** nunca subas tu archivo `.env` ni `secrets.toml` reales a GitHub
(el `.gitignore` incluido ya los excluye).

---

## Estructura del proyecto

```
sistema_deudores/
├── app.py                     # Login + Panel principal
├── pages/
│   ├── 1_Productos.py
│   ├── 2_Entradas.py
│   ├── 3_Salidas.py
│   ├── 4_Proveedores.py
│   └── 5_Deudores.py
├── utils/
│   ├── db.py                  # Conexión a Supabase
│   ├── auth.py                # Login / registro / recuperar contraseña / sesión
│   ├── queries.py             # Todas las consultas a la base de datos
│   ├── errors.py              # Manejo amigable de errores de conexión
│   ├── reports.py             # Exportar reportes a Excel
│   └── style.py                # Estilos visuales, logo y helper de WhatsApp
├── supabase_schema.sql        # Ejecutar en Supabase (tablas + seguridad)
├── requirements.txt
├── .env.example
└── .streamlit/
    ├── config.toml            # Tema visual
    └── secrets.toml.example
```

## Problemas comunes

- **"Faltan las credenciales de Supabase"** → revisa que tu `.env` (local)
  o tus Secrets (nube) tengan `SUPABASE_URL` y `SUPABASE_KEY` bien escritos,
  sin comillas de más ni espacios.
- **No puedo iniciar sesión / "Invalid login credentials"** → asegúrate de
  haber creado la cuenta primero en la pestaña "Crear cuenta", y si activaste
  la confirmación por correo, revisa tu bandeja de entrada.
- **Error de permisos al leer/guardar datos** → asegúrate de haber corrido
  completo el archivo `supabase_schema.sql` en el SQL Editor de Supabase.
