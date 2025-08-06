from typing import List
from app.database import get_connection
from app.models import DistrictOverlap


def query_districts_by_geometry(geom_wkt: str) -> List[DistrictOverlap]:
    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT name, province,
        ROUND(
            100 * CAST(ST_Area(ST_Intersection(geom, ST_GeomFromText(%s, 4326))) AS numeric) /
            CAST(ST_Area(ST_GeomFromText(%s, 4326)) AS numeric),
            2
        ) AS pct_overlap
    FROM districts
    WHERE ST_Intersects(geom, ST_GeomFromText(%s, 4326))
    ORDER BY pct_overlap DESC;
    """

    cur.execute(query, (geom_wkt, geom_wkt, geom_wkt))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        DistrictOverlap(district=row[0], province=row[1], pct_overlap=float(row[2]))
        for row in rows
    ]
