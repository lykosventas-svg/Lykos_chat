"""
Seed Data para ChromaDB
=======================

Agregue aquí los documentos que desea cargar en ChromaDB.
Cada documento es un diccionario con:
  - "content": El texto del documento (requerido)
  - "metadata": Metadatos opcionales (diccionario con cualquier información adicional)

Los documentos se cargarán automáticamente al iniciar la aplicación.
Si ChromaDB ya tiene datos, NO se volverán a cargar (evita duplicados).

Ejemplo:
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
"""

documentos = [
    """Potable: aquella destinada para el consumo humano.
Dulce: se encuentra en la superficie terrestre de manera natural, así como en ecosistemas subterráneos.
Salada: posee una concentración de sales minerales disueltas de cerca del 35%. Se encuentra en océanos y mares.""",
    """Salobre: tiene más sales disueltas que la dulce, pero menos que la salada.
Dura: aquella que contiene un alto nivel de minerales disueltos.
Blanda: en ella se encuentra disuelta una mínima cantidad de minerales.""",
    """Destilada: cuando ha sido purificada o limpiada mediante destilación.""",
    """Salada: posee una concentración de sales minerales disueltas de cerca del 35%. Se encuentra en océanos y mares. Salobre: tiene más sales disueltas que la dulce, pero menos que la salada. Dura: aquella que contiene un alto nivel de minerales disueltos. Blanda: en ella se encuentra disuelta una mínima cantidad de minerales. Destilada: cuando ha sido purificada o limpiada mediante destilación.
Residuales: cualquier tipo de agua cuya calidad está afectada negativamente por la influencia del ser humano.
Negras: contaminadas con heces u orina.""",
    """Grises: también conocida como agua usada, es aquella que proviene del uso doméstico.
Cruda o bruta: no ha recibido ningún tratamiento y suele encontrarse en fuentes y reservas naturales.""",
""" Nueva:agua inventada""",
""" Cristalina:agua totalmente limpia y sin impurezas."""
]

metadatos = [
    {"seccion": "General", "tipo_contenido": "estadistica", "palabras_clave": "encuentra, potable, destinada, consumo"},
    {"seccion": "General", "tipo_contenido": "narrativa", "palabras_clave": "minerales, salobre, tiene, sales"},
    {"seccion": "General", "tipo_contenido": "narrativa", "palabras_clave": "destilada, sido, purificada, limpiada"},
    {"seccion": "General", "tipo_contenido": "estadistica", "palabras_clave": "minerales, salada, sales, disueltas"},
    {"seccion": "General", "tipo_contenido": "narrativa", "palabras_clave": "grises, conocida, agua, usada"},
    {"seccion": "General", "tipo_contenido": "narrativa", "palabras_clave": "nueva, agua, inventada"},
    {"seccion": "General", "tipo_contenido": "narrativa", "palabras_clave": "cristalina, agua, limpia, impurezas"}

]
ids = [
    "chunk_001",
    "chunk_002",
    "chunk_003",
    "chunk_004",
    "chunk_005",
    "chunk_006",
    "chunk_007"
]