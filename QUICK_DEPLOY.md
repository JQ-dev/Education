# ⚡ Despliegue Rápido (Quick Deploy)

## 🎯 Opción Más Rápida: Render (5 minutos)

### Paso 1: Preparar (1 min)
```bash
# Asegúrate de que tus datos estén en el repo
git status

# Si hay cambios:
git add .
git commit -m "Ready for deployment"
git push
```

### Paso 2: Deploy en Render (4 min)

1. **Ir a:** [dashboard.render.com](https://dashboard.render.com)
2. **Click:** "New +" → "Blueprint"
3. **Conectar** tu repositorio de GitHub
4. **Click:** "Apply" (Render detecta automáticamente `render.yaml`)
5. **Esperar** 5-10 minutos ⏳
6. **¡Listo!** 🎉 Obtén tu URL

---

## 🔗 URLs de Ejemplo

Después del despliegue, tu dashboard estará en:
- **Render:** `https://saber-analytics.onrender.com`
- **Railway:** `https://saber-analytics.up.railway.app`
- **Fly.io:** `https://saber-analytics.fly.dev`

---

## ✅ Checklist Pre-Deployment

Antes de desplegar, verifica:

- [ ] ✅ `requirements.txt` existe y tiene todas las dependencias
- [ ] ✅ `render.yaml` o `Procfile` existe
- [ ] ✅ Archivos `.parquet` o `.csv` están en el repo (o se cargarán después)
- [ ] ✅ `app.py` tiene `server = app.server`
- [ ] ✅ `runtime.txt` especifica Python 3.11
- [ ] ✅ Todo está commiteado y pusheado a GitHub

```bash
# Verificar rápidamente:
ls -la | grep -E "requirements.txt|render.yaml|Procfile|runtime.txt|app.py"
```

---

## 🧪 Probar Localmente Antes de Desplegar

```bash
# Instalar dependencias
pip install -r requirements.txt

# Probar con gunicorn (igual que en producción)
gunicorn app:server --bind 0.0.0.0:8052

# Abrir: http://localhost:8052
```

---

## 🐛 Solución Rápida de Problemas

### Error: "No module named 'gunicorn'"
```bash
pip install gunicorn
```

### Error: "Data files not found"
**Opción A:** Subir archivos pequeños (<100MB) al repo
```bash
git add *.parquet
git commit -m "Add data files"
git push
```

**Opción B:** Usar datos de muestra
1. Crea un archivo `sample_data_generator.py` (ver DEPLOYMENT_GUIDE.md)
2. Modifica `app.py` para cargar datos de muestra si no encuentra archivos reales

### Error: "Out of memory" en despliegue gratuito
- ✅ Reduce el tamaño de los datos (máx 100,000 registros)
- ✅ Usa solo datos agregados por colegio, no por estudiante
- ✅ Limita a 1 año de datos en lugar de múltiples años

---

## 📊 Optimización de Datos para Deployment

Si tus archivos son muy grandes (>50MB):

```python
# optimize_data.py
import pandas as pd

# Cargar datos completos
df = pd.read_parquet('Examen_Saber_11_SS_20241.parquet')

# Seleccionar muestra estratificada (10% por departamento)
df_sample = df.groupby('COLE_DEPTO_UBICACION', group_keys=False).apply(
    lambda x: x.sample(frac=0.1, random_state=42)
)

# Guardar versión optimizada
df_sample.to_parquet('data_for_deploy.parquet', compression='gzip')

print(f"Original: {len(df):,} registros")
print(f"Optimizado: {len(df_sample):,} registros")
print(f"Reducción: {(1 - len(df_sample)/len(df))*100:.1f}%")
```

Luego ejecuta:
```bash
python optimize_data.py
git add data_for_deploy.parquet
git commit -m "Add optimized data for deployment"
git push
```

---

## 🚀 Deploy con Un Solo Comando

### Para Fly.io:
```bash
flyctl launch --name saber-analytics
```

### Para Render (via CLI):
```bash
# Instalar Render CLI
brew tap render-oss/render
brew install render

# Deploy
render deploy
```

---

## 🔄 Actualizar después del Deploy

Después de hacer cambios:

```bash
git add .
git commit -m "Update dashboard features"
git push
```

**Auto-deploy:**
- ✅ Render: Auto-deploys desde GitHub
- ✅ Railway: Auto-deploys desde GitHub
- ⚠️ Fly.io: Requiere `flyctl deploy` manual

---

## 📞 Soporte

Si tienes problemas:

1. **Revisar logs** en la plataforma
2. **Consultar** DEPLOYMENT_GUIDE.md para detalles
3. **Verificar** que todas las dependencias estén en requirements.txt
4. **Probar localmente** primero con gunicorn

---

## 🎊 ¡Éxito!

Cuando veas esto en los logs:
```
✓ Built successfully
✓ Health check passed
✓ Live at: https://tu-app.onrender.com
```

**¡Tu dashboard está en línea! 🎉**

Comparte tu URL con colegas y comienza a analizar datos educativos.

---

## 💡 Próximos Pasos

1. [ ] Configurar dominio personalizado
2. [ ] Agregar autenticación de usuarios
3. [ ] Configurar base de datos para usuarios (PostgreSQL gratuita en Render)
4. [ ] Agregar Google Analytics
5. [ ] Optimizar rendimiento con caché

Ver **DEPLOYMENT_GUIDE.md** para instrucciones detalladas.
