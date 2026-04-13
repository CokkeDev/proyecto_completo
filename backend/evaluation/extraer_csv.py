import csv
from qdrant_client import QdrantClient

COLLECTION_NAME = "proyectos_ley"

client = QdrantClient(host="localhost", port=6333)

offset = None
rows = []

while True:
    response = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=100,
        with_payload=True,
        with_vectors=False,
        offset=offset,
    )

    points, next_offset = response

    for p in points:
        payload = p.payload or {}
        rows.append({
            "id": str(p.id),
            "boletin": payload.get("boletin", ""),
            "suma": payload.get("suma", ""),
            "titulo": payload.get("titulo", ""),
            "categoria": payload.get("categoria", ""),
            "categorias": payload.get("categorias", ""),
        })

    if next_offset is None:
        break

    offset = next_offset

with open("boletines_qdrant.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["id", "boletin", "suma", "titulo", "categoria", "categorias"]
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Exportados {len(rows)} registros a boletines_qdrant.csv")