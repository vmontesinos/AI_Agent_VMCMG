# AI Agent VMCMG 🚀

Entorno de automatización completo con **n8n**, **PostgreSQL**, **Qdrant**, **Nginx** y un módulo de **integración con Strava** para un agente IA de entrenamiento personal.

## Arquitectura

```
                 ┌──────────┐    HTTP Request    ┌──────────────┐
Internet ──────► │  Nginx   │ ─────────────────► │     n8n      │
                 └──────────┘                    └──────┬───────┘
                                                        │ POST /sync
                                                        ▼
                                                 ┌──────────────┐
                                                 │ strava_sync  │  ← Python sidecar
                                                 │ (webhook:8080)│
                                                 └──────┬───────┘
                                                        │ Upsert
                                                        ▼
                                                 ┌──────────────┐
                                                 │  PostgreSQL  │ ◄── AI Trainer queries
                                                 └──────────────┘
```

## Servicios Docker

| Contenedor | Imagen | Puerto | Función |
|---|---|---|---|
| `n8n` | n8nio/n8n:latest | 5678 (interno) | Automatización de flujos |
| `db_postgres` | postgres:15 | 5432 (localhost) | Base de datos principal |
| `qdrant` | qdrant/qdrant | 6333 (interno) | Vectores para IA (RAG) |
| `nginx` | nginx:alpine | 80/443 | Proxy inverso + SSL |
| `strava_sync` | python:3.12-slim | 8080 (interno) | Importador de Strava |

---

## 🏃 Módulo Strava – AI Personal Trainer

### ¿Qué hace?

El contenedor `strava_sync` sincroniza automáticamente las actividades de Strava con PostgreSQL. El agente de IA en n8n puede consultar la base de datos para responder preguntas como:

- _"¿Cuántos km corrí en marzo de 2025?"_
- _"¿Cuál fue mi ritmo cardíaco medio en las salidas largas?"_
- _"Compara mi rendimiento de este mes vs el anterior."_

### Esquema de la base de datos

Tabla `strava_activities` en `entrenador_db`:

| Campo | Tipo | Descripción |
|---|---|---|
| `strava_id` | BIGINT PK | ID único de Strava |
| `type` | TEXT | Tipo de actividad (Run, Ride…) |
| `start_date` | TIMESTAMPTZ | Fecha/hora de inicio (UTC) |
| `distance` | FLOAT | Distancia en **metros** (÷1000 → km) |
| `moving_time` | INTEGER | Tiempo en **segundos** |
| `total_elevation_gain` | FLOAT | Desnivel en metros |
| `average_heartrate` | FLOAT | FC media (bpm) |
| `max_heartrate` | FLOAT | FC máxima (bpm) |
| `suffer_score` | INTEGER | Índice de sufrimiento Strava |
| `metadata` | JSONB | Datos extra (gear, elevación min/max) |
| `synced_at` | TIMESTAMPTZ | Timestamp de última sync |

### Sincronización inteligente

El script `sync_strava.py` es **incremental**: en cada ejecución consulta la fecha de la última actividad en la BD y sólo descarga lo nuevo. El primer arranque hace la carga histórica del último año.

### Archivos del módulo (`strava_app/`)

```
strava_app/
├── Dockerfile              # python:3.12-slim con dependencias
├── requirements.txt        # requests, psycopg2-binary, python-dotenv
├── .env                    # Credenciales (NO se sube a git)
├── .env.example            # Plantilla de variables
├── scripts/
│   ├── sync_strava.py      # Lógica principal de sincronización
│   ├── webhook_server.py   # Servidor HTTP que n8n activa vía POST /sync
│   ├── get_strava_auth_url.py     # Genera URL de autorización OAuth2
│   └── exchange_code_for_token.py # Intercambia código por refresh_token
└── sql/
    └── schema.sql          # DDL de la tabla strava_activities
```

---

## Guía de Despliegue

### 1. Instalar Docker

```bash
chmod +x scripts/instala_docker.sh
sudo ./scripts/instala_docker.sh
```

### 2. Configurar entornos

```bash
# Variables principales (n8n, PostgreSQL)
cp .env.example .env
# Editar con tus credenciales

# Variables de Strava
cp strava_app/.env.example strava_app/.env
# Añadir CLIENT_ID, CLIENT_SECRET y REFRESH_TOKEN
```

### 3. Autorización Strava (una sola vez)

```bash
# 3a. Generar URL de autorización
python3 strava_app/scripts/get_strava_auth_url.py
# → Visita la URL y autoriza la app

# 3b. Canjear código por token permanente
# Añade STRAVA_AUTH_CODE=codigo_del_redirect a strava_app/.env
python3 strava_app/scripts/exchange_code_for_token.py
# → Copia el REFRESH_TOKEN generado al .env
```

### 4. Levantar servicios

```bash
docker compose up -d
```

### 5. Carga inicial y verificación

```bash
# Verificar tabla
docker exec -t db_postgres psql -U entrenador -d entrenador_db -c "SELECT COUNT(*) FROM strava_activities;"
```

O desde n8n: importa `workflows/StravaDailySync.json` y ejecuta el **Manual Trigger**.

---

## Flujos n8n

| Workflow | Descripción |
|---|---|
| `StravaDailySync.json` | Sincroniza Strava → PostgreSQL. Schedule Trigger (07:00) + HTTP Request al sidecar. |

---

## Respaldo

| Dato | Estrategia |
|---|---|
| Flujos n8n | Exportar JSON → carpeta `workflows/` → `git commit` |
| Schema SQL | `sql/` en este repo |
| Datos (`data/`) | **NO en git**. Copiar manualmente con `scp`/`rsync` |
| Credenciales (`.env`) | **NO en git**. Gestionar con gestor de secretos o manual |

---

## Seguridad

- Los archivos `.env` están en `.gitignore`.
- La comunicación entre `n8n` y `strava_sync` se protege con `X-Sync-Secret`.
- PostgreSQL solo está expuesto en `127.0.0.1:5432`.

## Autor
Victor — [vmontesinos](https://github.com/vmontesinos)
