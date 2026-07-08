# 🤖 RAG Chatbot - ChromaDB + Huawei Cloud MaaS

Aplicación web con un chatbot basado en RAG (Retrieval-Augmented Generation) que utiliza **ChromaDB** como base de datos vectorial y **Huawei Cloud MaaS** (Model as a Service) como proveedor de LLM.

## Arquitectura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Frontend      │────▶│   FastAPI Backend │────▶│  ChromaDB   │
│   (HTML/CSS/JS) │◀────│   (Python)       │◀────│  (Vectores) │
└─────────────────┘     └────────┬─────────┘     └─────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Huawei Cloud   │
                        │  MaaS (LLM)     │
                        └─────────────────┘
```

## Características

- 🔍 **RAG (Retrieval-Augmented Generation)**: Busca documentos relevantes en ChromaDB y los usa como contexto para el LLM
- 🗄️ **ChromaDB**: Base de datos vectorial para almacenar y buscar documentos
- 🤖 **Huawei Cloud MaaS**: Servicio de IA compatible con OpenAI API
- ⚙️ **Configuración de MaaS**: Interfaz para configurar URL, API Key y Modelo
- 📄 **Gestión de Documentos**: Agregar documentos a ChromaDB desde `seed_data.py` en el código fuente
- 💬 **Chat Interactivo**: Interfaz de chat con indicador de escritura

## Requisitos

- Python 3.9+
- pip

## Instalación

1. Clonar o descargar el proyecto

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecutar la aplicación:
```bash
python run.py
```

4. Abrir el navegador en: [http://localhost:8000](http://localhost:8000)

## Uso

### 1. Configurar MaaS

Haga clic en el botón ⚙️ (engranaje) en la esquina superior derecha y configure:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **URL del Endpoint** | URL base del servicio MaaS | `https://maas-api.xxx.myhuaweicloud.com` |
| **API Key** | Clave de autenticación de Huawei Cloud | `MI_API_KEY` |
| **Modelo de IA** | Nombre del modelo a utilizar | `qwen2.5-72b-instruct` |

> **Nota**: La API de MaaS es compatible con OpenAI, por lo que se añade `/v1` automáticamente a la URL.

### 2. Agregar Documentos

Edite el archivo **`seed_data.py`** en la raíz del proyecto para agregar documentos a ChromaDB. Cada documento es un diccionario con `content` (texto) y `metadata` (metadatos opcionales):

```python
DOCUMENTS = [
    {
        "content": "Python es un lenguaje de programación de alto nivel...",
        "metadata": {"source": "wikipedia", "topic": "python"}
    },
    {
        "content": "FastAPI es un framework web moderno y rápido...",
        "metadata": {"source": "docs", "topic": "fastapi"}
    },
]
```

Los documentos se cargan automáticamente al iniciar la aplicación. Si ChromaDB ya tiene datos, no se vuelven a cargar (evita duplicados). Para forzar la recarga, elimine la carpeta `chroma_data/` y reinicie.

### 3. Hacer Preguntas

Escriba su pregunta en el campo de texto y presione Enter o el botón de enviar. El chatbot:

1. Busca documentos relevantes en ChromaDB
2. Si la base de datos está vacía, responde: *"No hay información en ChromaDB"*
3. Si hay documentos, los usa como contexto para generar una respuesta con el LLM de MaaS

## Estructura del Proyecto

```
Chatbot/
├── app/
│   ├── __init__.py
│   ├── config.py          # Gestión de configuración (MaaS)
│   ├── database.py        # Gestión de ChromaDB
│   ├── llm_service.py     # Servicio LLM (Huawei Cloud MaaS)
│   └── main.py            # FastAPI application y rutas
├── static/
│   ├── index.html         # Frontend HTML
│   ├── style.css          # Estilos CSS
│   └── app.js             # JavaScript del frontend
├── seed_data.py           # ⭐ Datos iniciales para ChromaDB (editar aquí)
├── chroma_data/           # Datos de ChromaDB (se crea automáticamente)
├── config.json            # Configuración guardada (se crea automáticamente)
├── requirements.txt       # Dependencias Python
├── run.py                 # Punto de entrada
└── README.md              # Este archivo
```

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/chat` | Enviar mensaje al chatbot |
| GET | `/api/config` | Obtener configuración MaaS |
| POST | `/api/config` | Guardar configuración MaaS |
| POST | `/api/config/test` | Probar conexión MaaS |
| GET | `/api/stats` | Estadísticas de la base de datos |
