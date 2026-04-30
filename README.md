# Buscador Semántico de Proyectos de Ley — Senado de Chile

Sistema de búsqueda semántica y clasificación automática de proyectos de ley chilenos (2020–2026).  
Desarrollado como proyecto de tesis de pregrado.

---

## Descripción

El sistema descarga, clasifica, vectoriza e indexa proyectos de ley del Senado de Chile usando:

- **ClosedSetClassifier**: Clasificador de conjunto cerrado en 3 capas (reglas regex → keywords → embeddings semánticos). Solo asigna categorías definidas en la taxonomía manual; si no hay match, etiqueta el proyecto como `POR_CLASIFICAR`.
- **BAAI/bge-m3**: Modelo de embeddings multilingüe de 1024 dimensiones para búsqueda semántica.
- **Qdrant**: Base de datos vectorial para almacenamiento y búsqueda por similitud.
- **FastAPI**: Backend REST con documentación Swagger automática.
- **Frontend estático**: Interfaz web en HTML/CSS/JS puro, sin framework.

---

## Requisitos Previos

| Herramienta | Versión mínima |
|-------------|----------------|
| Python      | 3.10+          |
| Docker      | 20+            |
| RAM libre   | ~6 GB (modelo BAAI/bge-m3 en fp16 ≈ 570 MB + Qdrant) |

---

## Instalación y Arranque

### 1. Clonar y preparar entorno virtual

```bash
git clone <url-del-repositorio>
cd proyecto_completo

python -m venv tesis
# Windows:
.\tesis\Scripts\activate
# macOS/Linux:
source tesis/bin/activate
```

### 2. Instalar dependencias Python

```bash
pip install -r backend/requirements.txt
```

> **Nota GPU**: Si tienes CUDA instalado, instala PyTorch con soporte GPU antes de los demás paquetes:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cu118
> ```

### 3. Levantar Qdrant con Docker

```bash
docker run -d \
  -p 6333:6333 \
  -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage \
  --name qdrant \
  qdrant/qdrant
```

Verificar que Qdrant responde: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

### 4. Configurar variables de entorno

```bash
cp backend/.env.example backend/.env
# Editar backend/.env si necesitas cambiar host/puerto de Qdrant u otros parámetros
```

Variables importantes en `.env`:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `QDRANT_HOST` | `localhost` | Host de Qdrant |
| `QDRANT_PORT` | `6333` | Puerto de Qdrant |
| `QDRANT_IN_MEMORY` | `false` | `true` para testing sin Docker |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Modelo de embeddings (no cambiar) |
| `CLASSIFICATION_THRESHOLD` | `0.45` | Umbral base (el ClosedSetClassifier usa umbrales propios) |

### 5. Iniciar el backend

```bash
# Desde la raíz del proyecto (no desde backend/)
python3 -m uvicorn backend.main:app --reload --port 8000
```

El servidor arranca, carga el modelo BAAI/bge-m3 (primera vez: descarga ~1.4 GB) y pre-calcula los centroides del ClosedSetClassifier.

Swagger UI disponible en: [http://localhost:8000/docs](http://localhost:8000/docs)

### 6. Abrir el frontend

```bash
cd HostingTesis
python3 -m http.server 5500
```

Abrir: [http://localhost:5500/Buscador.html](http://localhost:5500/Buscador.html)

---

## Ingesta de Datos

### Opción A — Demo: últimos 15 proyectos con texto completo (recomendada para empezar)

```bash
curl -X POST http://localhost:8000/api/v1/ingest/demo
```

- Descarga los 15 proyectos más recientes de la API del Senado.
- Para cada uno, descarga el PDF del proyecto y extrae el texto completo.
- Clasifica con **ClosedSetClassifier** usando el texto completo del documento.
- Retorna los resultados inmediatamente (no en background).
- Guarda los resultados en Qdrant.

### Opción B — Pipeline completo (2020–2026)

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/run?skip_existing=true"
```

- Descarga todos los proyectos del rango configurado en `.env` (puede tardar 10–30 min).
- Clasifica usando SUMA + MATERIAS (sin descargar PDFs).
- Se ejecuta en background; consultar estado en:

```bash
curl http://localhost:8000/api/v1/ingest/status
```

---

## API — Endpoints Principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/v1/ingest/demo` | Ingesta los últimos 15 proyectos con texto completo de PDF |
| `POST` | `/api/v1/ingest/run` | Pipeline completo en background |
| `GET`  | `/api/v1/ingest/status` | Estado del pipeline y colección Qdrant |
| `GET`  | `/api/v1/search/semantic?q=texto` | Búsqueda semántica por lenguaje natural |
| `GET`  | `/api/v1/search/hybrid?q=texto&categoria=CAT` | Búsqueda semántica + filtros |
| `GET`  | `/api/v1/search/structured?categoria=CAT` | Búsqueda solo por filtros (sin vector) |
| `GET`  | `/api/v1/search/detail/{boletin}` | Detalle de un proyecto por boletín |
| `GET`  | `/api/v1/search/categories` | Taxonomía completa disponible |
| `POST` | `/api/v1/classify` | Clasificar un texto arbitrario |
| `POST` | `/api/v1/eval/run` | Ejecutar suite de evaluación completa |
| `GET`  | `/health` | Estado del sistema (Qdrant + modelo) |

Documentación interactiva completa: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Arquitectura del Sistema

```
proyecto_completo/
├── HostingTesis/                  # Frontend estático
│   ├── Buscador.html              # Página principal de búsqueda
│   ├── Acerca.html                # Página "Acerca de"
│   ├── ScriptBsucador.js          # Lógica del frontend
│   └── stiloBuscador.css          # Estilos
│
└── backend/
    ├── main.py                    # App FastAPI, CORS, startup
    ├── config.py                  # Settings desde .env (Pydantic)
    ├── requirements.txt
    │
    ├── api/
    │   ├── routes_search.py       # Endpoints de búsqueda
    │   ├── routes_ingest.py       # Endpoints de ingesta (incluye /demo)
    │   ├── routes_classify.py     # Endpoint de clasificación individual
    │   └── routes_eval.py         # Endpoints de evaluación
    │
    ├── classification/
    │   ├── closed_set_classifier.py   ← NUEVO: clasificador principal
    │   ├── hybrid_classifier.py       # Clasificador legado (mantenido)
    │   ├── rule_classifier.py         # Capa de reglas (usada internamente)
    │   ├── embedding_classifier.py    # Capa semántica (usada internamente)
    │   └── models.py                  # Pydantic models (ClassificationMatch, ClosedSetResult, etc.)
    │
    ├── ingestion/
    │   ├── pipeline.py            # Orquestador ETL
    │   ├── fetcher.py             # Descarga de API del Senado
    │   ├── document_fetcher.py    ← NUEVO: descarga y extrae texto de PDFs
    │   ├── normalizer.py          # Limpieza y normalización de campos
    │   └── chunker.py             # División de textos largos en chunks
    │
    ├── taxonomy/
    │   ├── taxonomy_data.py       # TAXONOMY: fuente de verdad única (11 categorías)
    │   ├── manual_taxonomy.py     # Interfaz de acceso a TAXONOMY
    │   └── emergent_taxonomy.py   # Detector de clusters (análisis exploratorio, no en pipeline)
    │
    ├── embeddings/
    │   └── encoder.py             # BGEEncoder singleton (BAAI/bge-m3)
    │
    ├── qdrant/
    │   ├── client.py              # QdrantManager: upsert, búsquedas, filtros
    │   └── schemas.py             # Nombre de colección y dimensiones
    │
    ├── search/
    │   └── searcher.py            # SearchEngine: semántica, estructurada, híbrida
    │
    └── evaluation/
        ├── evaluator.py           # Evaluación de clasificación (F1, precision, recall)
        ├── metrics.py             # Métricas: coseno, ROUGE-L
        ├── hypothesis1_evaluator.py  # Evaluación específica hipótesis de tesis
        └── ground_truth_sample.jsonl # 200+ proyectos anotados manualmente
```

---

## Clasificador de Conjunto Cerrado (ClosedSetClassifier)

El `ClosedSetClassifier` reemplaza al sistema híbrido anterior. **No puede inventar ni inferir categorías** fuera de las definidas en `taxonomy_data.py`.

### Taxonomía (11 categorías top-level)

| Código | Categoría |
|--------|-----------|
| `DERECHO_LABORAL_EMPLEO` | Derecho Laboral y Empleo |
| `SALUD_PUBLICA` | Salud Pública |
| `EDUCACION` | Educación |
| `MEDIO_AMBIENTE` | Medio Ambiente y Recursos Naturales |
| `SEGURIDAD_JUSTICIA` | Seguridad Pública y Justicia |
| `ECONOMIA_FINANZAS` | Economía, Finanzas y Tributación |
| `DERECHOS_FUNDAMENTALES` | Derechos Fundamentales y Constitucionales |
| `VIVIENDA_URBANISMO` | Vivienda y Urbanismo |
| `TECNOLOGIA_INNOVACION` | Tecnología e Innovación |
| `INSTITUCIONALIDAD_ESTADO` | Institucionalidad del Estado |
| `TRANSPORTE` | Transporte y Movilidad |

### Lógica de clasificación por capas

```
Texto del proyecto
       │
       ▼
┌─────────────────────────────┐
│  Capa 1: Reglas Regex       │  ← reglas_semanticas de taxonomy_data.py
│  Confianza: 0.60 + 0.08/regla│    Acepta con ≥1 match
└────────────┬────────────────┘
             │ sin match
             ▼
┌─────────────────────────────┐
│  Capa 2: Keywords           │  ← keywords ponderadas de taxonomy_data.py
│  Umbral: score ≥ 0.30       │    Frases pesan 2, palabras sueltas pesan 1
└────────────┬────────────────┘
             │ sin match
             ▼
┌─────────────────────────────┐
│  Capa 3: Embeddings         │  ← BAAI/bge-m3 vs. centroides prototipo
│  Umbral: coseno ≥ 0.70      │    Solo si Capas 1 y 2 fallan
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  Validación de Negativos    │  ← ejemplos_negativos de taxonomy_data.py
│  Rechaza si sim_neg > sim_pos│   Evita falsos positivos
└────────────┬────────────────┘
             │
             ▼
     ┌───────┴────────┐
     │                │
  clasificado    POR_CLASIFICAR
  (primary +     (revisión manual)
   secondary)
```

### Ejemplo de respuesta del endpoint `/ingest/demo`

```json
{
  "total_procesados": 15,
  "clasificados": 12,
  "por_clasificar": 3,
  "pdf_descargados": 10,
  "resultados": [
    {
      "boletin": "17890-13",
      "suma": "Modifica el Código del Trabajo en materia de...",
      "fecha_ingreso": "2026-04-15",
      "pdf_status": "ok",
      "palabras_analizadas": 1500,
      "texto_fuente": "documento_completo",
      "estado_clasificacion": "clasificado",
      "primary": {
        "categoria_id": "DERECHO_LABORAL_EMPLEO",
        "categoria_label": "Derecho Laboral y Empleo",
        "subcategoria_id": "CONTRATOS_LABORALES",
        "subcategoria_label": "Contratos y relaciones laborales",
        "metodo_match": "regla_regex",
        "confianza": 0.76,
        "matched_rules": ["código\\s+del\\s+trabajo", "despido\\s+..."]
      },
      "secondary": []
    }
  ]
}
```

---

## Evaluación

```bash
# Ejecutar evaluación completa (requiere ground_truth_sample.jsonl)
curl -X POST http://localhost:8000/api/v1/eval/run

# Resultados en:
# backend/evaluation/results/full_evaluation.json
# backend/evaluation/results/metrics_hybrid.json
# backend/evaluation/results/metrics_embeddings.json
```

Métricas evaluadas:
- **Clasificación**: F1-score (weighted), precision, recall — `sklearn.MultiLabelBinarizer`
- **Retrieval semántico**: cosine similarity promedio, recall@k
- **Generación**: ROUGE-L para explicaciones

---

## Desarrollo y Testing

```bash
# Tests unitarios
pytest backend/tests/

# Clasificar un texto directamente (sin ingestar)
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{"boletin": "test-01", "suma": "Modifica el Código del Trabajo para reducir la jornada laboral"}'

# Testing con Qdrant en memoria (sin Docker)
# En backend/.env: QDRANT_IN_MEMORY=true
```

---

## Fuente de Datos

API REST pública del Senado de Chile:

```
https://restsil-ventanillaunica.senado.cl/v3/proyectos
  ?desde=18/03/2020
  &hasta=30/03/2026
  &offset=0
  &limit=200
  &order=asc
```

Campos utilizados: `ID_PROYECTO`, `BOLETIN`, `SUMA`, `FECHA_INGRESO`, `INICIATIVA`, `TIPO`, `CAMARA_ORIGEN`, `AUTORES`, `MATERIAS`, `ETAPA`, `DOCUMENTO`, `LINK_PROYECTO_LEY`

El campo `DOCUMENTO` contiene la URL al PDF del proyecto completo, usado por el modo de texto completo.

---

## Tecnologías

| Componente | Tecnología |
|------------|------------|
| Backend API | FastAPI + Uvicorn |
| Embeddings | BAAI/bge-m3 (FlagEmbedding) — 1024 dims |
| Vector DB | Qdrant |
| PDF parsing | pypdf |
| ML | scikit-learn, numpy, scipy |
| Clustering (exploratorio) | HDBSCAN + UMAP |
| Frontend | HTML5 + CSS3 + JavaScript vanilla |
