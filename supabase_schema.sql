-- ============================================================
-- Esquema para el sistema de Inventario + Fiados
-- Ejecutar en Supabase: Panel del proyecto > SQL Editor > New query
-- ============================================================

create extension if not exists pgcrypto;

-- ---------- Proveedores ----------
create table if not exists proveedores (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    nombre text not null,
    telefono text,
    email text,
    notas text,
    created_at timestamptz default now()
);

-- ---------- Productos ----------
create table if not exists productos (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    nombre text not null,
    categoria text,
    stock numeric not null default 0,
    stock_minimo numeric not null default 5,
    precio_compra numeric default 0,
    precio_venta numeric default 0,
    proveedor_id uuid references proveedores(id) on delete set null,
    created_at timestamptz default now()
);

-- Migración: si ya habías creado la tabla productos antes, esto agrega
-- la columna nueva sin borrar tus datos (no hace nada si ya existe).
alter table productos add column if not exists stock_minimo numeric not null default 5;

-- ---------- Entradas (ingresos de stock) ----------
create table if not exists entradas (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    producto_id uuid not null references productos(id) on delete cascade,
    proveedor_id uuid references proveedores(id) on delete set null,
    cantidad numeric not null,
    precio_unitario numeric default 0,
    notas text,
    fecha timestamptz default now()
);

-- ---------- Salidas (ventas / egresos de stock) ----------
create table if not exists salidas (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    producto_id uuid not null references productos(id) on delete cascade,
    cantidad numeric not null,
    precio_unitario numeric default 0,
    notas text,
    fecha timestamptz default now()
);

-- ---------- Deudores ----------
create table if not exists deudores (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    nombre text not null,
    telefono text,
    notas text,
    created_at timestamptz default now()
);

-- ---------- Deudas (cargos al deudor) ----------
create table if not exists deudas (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    deudor_id uuid not null references deudores(id) on delete cascade,
    monto numeric not null,
    descripcion text,
    fecha timestamptz default now()
);

-- ---------- Abonos (pagos del deudor) ----------
create table if not exists abonos (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    deudor_id uuid not null references deudores(id) on delete cascade,
    monto numeric not null,
    fecha timestamptz default now()
);

-- ============================================================
-- Row Level Security: cada usuario solo ve/edita sus propios datos
-- ============================================================

alter table proveedores enable row level security;
alter table productos   enable row level security;
alter table entradas    enable row level security;
alter table salidas     enable row level security;
alter table deudores    enable row level security;
alter table deudas      enable row level security;
alter table abonos      enable row level security;

do $$
declare
    t text;
begin
    foreach t in array array['proveedores','productos','entradas','salidas','deudores','deudas','abonos']
    loop
        execute format('
            create policy "select_own_%1$s" on %1$s for select
                using (auth.uid() = user_id);
        ', t);
        execute format('
            create policy "insert_own_%1$s" on %1$s for insert
                with check (auth.uid() = user_id);
        ', t);
        execute format('
            create policy "update_own_%1$s" on %1$s for update
                using (auth.uid() = user_id);
        ', t);
        execute format('
            create policy "delete_own_%1$s" on %1$s for delete
                using (auth.uid() = user_id);
        ', t);
    end loop;
end $$;
