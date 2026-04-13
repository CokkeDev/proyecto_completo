# Inicio rápido — MVP

## 1. Requisitos previos

- Python 3.10+
- Docker Desktop (para Qdrant)
- ~4 GB RAM libre (el modelo BAAI/bge-m3 pesa ~570 MB en fp16)

## 1.1 Si esta tesis el entorno esta activado, lo cual debe de ejecutarlo con el siguiente comando:

```bash
python3 -m venv tesis
```

## 2. Instalar dependencias

```bash
cd backend
pip install -r requirements.txt
```

> Nota: `torch` puede requerir instalar la versión correcta para tu GPU/CPU.
> Si tienes CUDA: `pip install torch --index-url https://download.pytorch.org/whl/cu118`

## 3. Iniciar Qdrant con Docker

```bash
docker run -d -p 6333:6333 -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage \
  --name qdrant qdrant/qdrant
```

Verificar: http://localhost:6333/dashboard

## 4. Copiar configuración

```bash
cp backend/.env.example backend/.env
# Editar .env si es necesario
```

## 5. Iniciar el backend 

```bash
cd Proyecto_completo
python3 -m uvicorn backend.main:app --reload --port 8000
```

Verificar: http://localhost:8000/docs (Swagger UI)

## 6. Ejecutar ingesta

```bash
# Desde Swagger UI o curl:
curl -X POST http://localhost:8000/api/v1/ingest/run
```

La primera ingesta descarga todos los proyectos (2020-2026), los clasifica
con el sistema híbrido y los almacena en Qdrant. Puede tomar 10-30 minutos
dependiendo del hardware.

## 7. Abrir el frontend

Abrir `HostingTesis/Buscador.html` directamente en el navegador, o servir
con un servidor local:

```bash
cd HostingTesis
python3 -m http.server 5500
# http://localhost:5500/Buscador.html
```

## 8. Ejecutar evaluación

```bash
curl -X POST http://localhost:8000/api/v1/eval/run
```

Los resultados se guardan en `backend/evaluation/results/`.

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/search/semantic?q=texto` | Búsqueda semántica |
| GET | `/api/v1/search/hybrid?q=texto&categoria=CAT` | Búsqueda híbrida |
| GET | `/api/v1/search/structured?categoria=CAT` | Solo filtros |
| GET | `/api/v1/search/detail/{boletin}` | Detalle |
| GET | `/api/v1/search/categories` | Taxonomía completa |
| POST | `/api/v1/classify` | Clasificar un texto |
| POST | `/api/v1/ingest/run` | Pipeline de ingesta |
| POST | `/api/v1/eval/run` | Evaluación completa |
| POST | `/api/v1/eval/cosine` | Similitud coseno |
| POST | `/api/v1/eval/rouge` | ROUGE-L |
