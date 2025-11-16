# 🚀 Guía de Despliegue en la Nube (Deployment Guide)

Esta guía te ayudará a desplegar tu Plataforma de Analítica Educativa SABER en servicios gratuitos de la nube.

---

## 📋 Tabla de Contenidos

1. [Opción 1: Render (Recomendado - Más Fácil)](#opción-1-render-recomendado)
2. [Opción 2: Railway](#opción-2-railway)
3. [Opción 3: Fly.io](#opción-3-flyio)
4. [Preparación de Datos](#preparación-de-datos)
5. [Solución de Problemas](#solución-de-problemas)

---

## ✅ Prerequisitos

Antes de comenzar, asegúrate de tener:
- ✅ Una cuenta de GitHub (gratis)
- ✅ Tu código subido a un repositorio de GitHub
- ✅ Archivos de datos (`.parquet` o `.csv`) listos

---

## 🎯 Opción 1: Render (Recomendado)

**Ventajas:** Gratis, fácil configuración, auto-deploys desde GitHub

### Paso 1: Preparar el Repositorio

1. **Sube tus archivos de datos al repositorio:**
   ```bash
   git add *.parquet
   git commit -m "Add data files for deployment"
   git push
   ```

2. **Verifica que tienes estos archivos:**
   - ✅ `app.py` (aplicación principal con todas las funcionalidades)
   - ✅ `landing_page.py`
   - ✅ `requirements.txt`
   - ✅ `render.yaml`
   - ✅ Archivos de datos (`.parquet`)

### Paso 2: Crear Cuenta en Render

1. Ve a [render.com](https://render.com)
2. Click en **"Get Started for Free"**
3. Regístrate con tu cuenta de GitHub

### Paso 3: Desplegar la Aplicación

#### Método A: Usando el Archivo render.yaml (Más Fácil)

1. En el dashboard de Render, click **"New +"** → **"Blueprint"**
2. Conecta tu repositorio de GitHub
3. Render detectará automáticamente el archivo `render.yaml`
4. Click **"Apply"**
5. ¡Espera 5-10 minutos y tu app estará lista! 🎉

#### Método B: Configuración Manual

1. En el dashboard de Render, click **"New +"** → **"Web Service"**
2. Conecta tu repositorio de GitHub
3. Configura:
   - **Name:** `saber-analytics`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:server --bind 0.0.0.0:$PORT`
   - **Plan:** `Free`
4. Click **"Create Web Service"**
5. Espera a que termine el despliegue

### Paso 4: Acceder a tu Aplicación

Una vez desplegada, Render te dará una URL como:
```
https://saber-analytics-xxxx.onrender.com
```

**Nota:** El servicio gratuito "duerme" después de 15 minutos de inactividad. La primera carga puede tardar 30-60 segundos.

---

## 🚂 Opción 2: Railway

**Ventajas:** Interfaz moderna, $5 USD gratis mensuales

### Paso 1: Crear Cuenta

1. Ve a [railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Regístrate con GitHub

### Paso 2: Desplegar

1. Click **"Deploy from GitHub repo"**
2. Selecciona tu repositorio
3. Railway detectará automáticamente que es Python
4. Agrega las variables de entorno (si necesitas):
   - Click en **"Variables"**
   - Agrega: `PORT=8080` (opcional)
5. Railway automáticamente:
   - Instala dependencias desde `requirements.txt`
   - Ejecuta el comando del `Procfile`
6. Click en **"Deploy"**

### Paso 3: Obtener URL

1. En la pestaña **"Settings"**
2. Click en **"Generate Domain"**
3. Tu URL será: `https://saber-analytics.up.railway.app`

---

## ✈️ Opción 3: Fly.io

**Ventajas:** Muy rápido, 3 aplicaciones gratis

### Paso 1: Instalar Fly CLI

```bash
# En macOS
brew install flyctl

# En Linux
curl -L https://fly.io/install.sh | sh

# En Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### Paso 2: Autenticarse

```bash
flyctl auth signup   # Para nueva cuenta
# o
flyctl auth login    # Para cuenta existente
```

### Paso 3: Crear Archivo fly.toml

Crea un archivo `fly.toml` en tu repositorio:

```toml
app = "saber-analytics"
primary_region = "mia"  # Miami - más cercano a Colombia

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
```

### Paso 4: Desplegar

```bash
# Desde el directorio del proyecto
flyctl launch

# Sigue las instrucciones:
# - ¿Crear nueva app? Sí
# - ¿Nombre? saber-analytics (o deja que genere uno)
# - ¿Región? Miami (mia) - cercana a Colombia
# - ¿Base de datos? No
# - ¿Deploy ahora? Sí

# Tu app estará en: https://saber-analytics.fly.dev
```

---

## 📊 Preparación de Datos

### Reducir Tamaño de Datos (Importante para Depliegue Gratuito)

Los servicios gratuitos tienen límites de almacenamiento. Optimiza tus datos:

```python
import pandas as pd

# Cargar datos
df = pd.read_parquet('Examen_Saber_11_SS_20241.parquet')

# Seleccionar solo columnas necesarias
columns_to_keep = [
    'COLE_COD_DANE_ESTABLECIMIENTO',
    'COLE_NOMBRE_ESTABLECIMIENTO',
    'COLE_DEPTO_UBICACION',
    'COLE_MCPIO_UBICACION',
    'COLE_NATURALEZA',
    'COLE_AREA_UBICACION',
    'COLE_GENERO',
    'COLE_CARACTER',
    'PUNT_LECTURA_CRITICA',
    'PUNT_MATEMATICAS',
    'PUNT_C_NATURALES',
    'PUNT_SOCIALES_CIUDADANAS',
    'PUNT_INGLES',
    'PUNT_GLOBAL'
]

df_optimized = df[columns_to_keep]

# Guardar versión optimizada
df_optimized.to_parquet('data_optimized.parquet', compression='gzip')
```

### Usar Datos de Muestra para Testing

Crea un archivo `sample_data.py`:

```python
import pandas as pd
import numpy as np

# Generar datos de muestra para testing
np.random.seed(42)
n_schools = 100

sample_data = pd.DataFrame({
    'COLE_COD_DANE_ESTABLECIMIENTO': range(1, n_schools+1),
    'COLE_NOMBRE_ESTABLECIMIENTO': [f'Colegio {i}' for i in range(1, n_schools+1)],
    'COLE_DEPTO_UBICACION': np.random.choice(['CUNDINAMARCA', 'ANTIOQUIA', 'VALLE'], n_schools),
    'COLE_MCPIO_UBICACION': np.random.choice(['BOGOTÁ', 'MEDELLÍN', 'CALI'], n_schools),
    'COLE_NATURALEZA': np.random.choice(['OFICIAL', 'NO OFICIAL'], n_schools),
    'COLE_AREA_UBICACION': np.random.choice(['URBANO', 'RURAL'], n_schools),
    'PUNT_MATEMATICAS_mean': np.random.normal(250, 50, n_schools),
    'PUNT_LECTURA_CRITICA_mean': np.random.normal(250, 50, n_schools),
})

sample_data.to_parquet('sample_data.parquet')
```

---

## 🐛 Solución de Problemas

### Error: "Out of Memory"

**Solución:**
1. Reduce el tamaño de tus archivos de datos
2. Usa solo datos agregados (por colegio, no por estudiante)
3. Limita a datos de un solo año

```python
# En app.py, agrega al inicio:
import os

# Detectar si estamos en producción
IS_PRODUCTION = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT')

if IS_PRODUCTION:
    # Cargar solo datos esenciales
    print("Cargando datos optimizados para producción...")
```

### Error: "Build Failed"

**Solución:**
1. Verifica que `requirements.txt` tenga todas las dependencias
2. Verifica que `app.py` tenga `server = app.server`
3. Asegúrate de que la versión de Python sea compatible (3.9-3.11)

### La App es Muy Lenta

**Causas comunes:**
1. **Demasiados datos:** Limita a 50,000-100,000 registros
2. **Sin caché:** Los servicios gratuitos no tienen memoria persistente
3. **Cold start:** El servicio gratuito "duerme" cuando no se usa

**Solución - Agregar caché simple:**

```python
# En app.py
from functools import lru_cache

@lru_cache(maxsize=32)
def load_cached_data():
    return load_saber11_2024_data()

# Usar:
df_students = load_cached_data()
```

### URL No Funciona

**Render:** Asegúrate de que el puerto sea `$PORT`, no un número fijo
**Railway:** Genera un dominio público en Settings
**Fly.io:** Verifica que `internal_port` coincida con el puerto de tu app

---

## 🔒 Mejores Prácticas de Seguridad

1. **No subas datos sensibles al repositorio público**
2. **Usa variables de entorno para configuración:**

```bash
# En Render/Railway, agrega:
ENV=production
DEBUG=False
```

3. **Agrega autenticación si es necesario** (usa el código de `auth_models.py`)

---

## 📈 Monitoreo y Logs

### Ver Logs en Render
1. Ve a tu servicio
2. Click en **"Logs"**
3. Verás logs en tiempo real

### Ver Logs en Railway
1. Click en tu servicio
2. Pestaña **"Deployments"**
3. Click en el deployment activo
4. Verás los logs

### Ver Logs en Fly.io
```bash
flyctl logs
```

---

## 🎉 ¡Listo!

Tu Plataforma de Analítica Educativa SABER ahora está desplegada y accesible desde cualquier lugar del mundo.

### Recursos Adicionales

- 📖 [Documentación de Render](https://render.com/docs)
- 📖 [Documentación de Railway](https://docs.railway.app)
- 📖 [Documentación de Fly.io](https://fly.io/docs)
- 📖 [Guía de Dash Deployment](https://dash.plotly.com/deployment)

### Compartir tu Dashboard

Una vez desplegado, comparte tu URL:
```
https://tu-app.onrender.com
```

**Nota:** Considera comprar un dominio personalizado (ej: `analytics.tudominio.com`) para un aspecto más profesional. La mayoría de plataformas permiten dominios personalizados en planes gratuitos.

---

## 💡 Siguientes Pasos

1. **Agregar autenticación** usando el sistema que creamos en `auth_models.py`
2. **Configurar dominio personalizado**
3. **Agregar Google Analytics** para monitorear uso
4. **Configurar alertas** para errores
5. **Optimizar rendimiento** con caché y compresión

¡Buena suerte con tu despliegue! 🚀
