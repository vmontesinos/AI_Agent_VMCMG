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

## Notas de Seguridad
- Asegúrate de cambiar todas las contraseñas por defecto en el archivo `.env`.
- La carpeta `data/` se crea automáticamente para persistir los datos de los contenedores.
- Los certificados SSL deben ser gestionados a través de Nginx o un proveedor externo.

## Autor
Victor - [vmontesinos](https://github.com/vmontesinos)
