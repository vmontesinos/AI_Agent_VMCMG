# AI Agent VMCMG 🚀

Este proyecto despliega un entorno de automatización basado en **n8n**, con base de datos **PostgreSQL**, motor de vectores **Qdrant** y un proxy inverso **Nginx**.

## Estructura del Proyecto

- `data/`: Almacenamiento persistente para bases de datos (ignorado en Git).
- `docs/`: Documentación y recursos.
- `nginx/`: Configuración del servidor Nginx.
- `pdfs/`: Carpeta para procesar documentos PDF.
- `scripts/`: Utilidades de instalación y mantenimiento.
- `sql/`: Scripts de migración y base de datos.
- `workflows/`: Exportaciones de flujos de n8n.

---

## Guía de Despliegue (Ubuntu Limpio)

Sigue estos pasos para desplegar el proyecto en un servidor Ubuntu recién instalado.

### 1. Preparar el Sistema e Instalar Docker

Primero, descarga el repositorio o sube el script de instalación. El proyecto incluye un script automatizado para instalar Docker y sus dependencias.

```bash
# Otorgar permisos de ejecución al script
chmod +x scripts/instala_docker.sh

# Ejecutar el script (requiere sudo)
sudo ./scripts/instala_docker.sh
```

### 2. Configuración de Entorno

Crea un archivo `.env` en la raíz del proyecto basado en tus necesidades. Debe contener las credenciales de la base de datos y la configuración de n8n.

```bash
# Ejemplo de contenido para .env
POSTGRES_USER=tu_usuario
POSTGRES_PASSWORD=tu_password
POSTGRES_DB=entrenador_db

N8N_BASIC_AUTH_USER=admin@tusitio.com
N8N_BASIC_AUTH_PASSWORD=tu_password_seguro
N8N_ENCRYPTION_KEY=una_clave_aleatoria_larga

N8N_HOST=tu-dominio.com
WEBHOOK_URL=https://tu-dominio.com/
```

### 3. Levantar los Servicios

Una vez configurado el entorno, levanta todos los contenedores usando Docker Compose:

```bash
sudo docker compose up -d
```

### 4. Verificar el Estado

Puedes comprobar que todos los servicios están corriendo correctamente con:

```bash
sudo docker compose ps
```

Los servicios disponibles serán:
- **n8n**: Automatización de flujos.
- **PostgreSQL**: Base de datos principal.
- **Qdrant**: Base de datos vectorial para IA.
- **Nginx**: Proxy inverso para acceso seguro.

---

## 💾 Respaldo y Recuperación (Backup & Restore)

Como el entorno se despliega "limpio" desde GitHub, aquí tienes cómo mantener tus datos a salvo:

### 1. Flujos de n8n (Workflows)
Para que tus flujos aparezcan en un servidor nuevo:
- **Exportar**: En tu n8n actual, ve a *Settings* > *Export Workflows* o usa la CLI de n8n para guardar los JSON en la carpeta `workflows/`.
- **Sincronizar**: Sube los cambios a GitHub (`git add workflows/*.json && git commit ...`).
- **Importar**: En el nuevo servidor, tras levantar Docker, importa los archivos JSON desde la interfaz de n8n.

### 2. Base de Datos (SQL)
Si tienes tablas o datos iniciales:
- **Exportar**: Guarda tus scripts de creación de tablas en `sql/migrations/`.
- **Automatizar**: Los archivos `.sql` que pongas en esa carpeta pueden ser configurados para ejecutarse al inicio de la base de datos si modificas el `docker-compose.yml`.

### 3. Datos Persistentes (Carpeta `data/`)
**¡IMPORTANTE!** La carpeta `data/` contiene tus bases de datos reales. 
- **NO se sube a GitHub** (por seguridad y tamaño).
- Si quieres mover tus datos de un servidor a otro, debes copiar esta carpeta manualmente (usando `scp` o `rsync`) por fuera de Git.

---

## Notas de Seguridad
- Asegúrate de cambiar todas las contraseñas por defecto en el archivo `.env`.
- La carpeta `data/` se crea automáticamente para persistir los datos de los contenedores.
- Los certificados SSL deben ser gestionados a través de Nginx o un proveedor externo.

## Autor
Victor - [vmontesinos](https://github.com/vmontesinos)
