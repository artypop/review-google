"""Retrouver une fiche Google à partir de son cid ou de son place_id.

Usage :
    python scripts/fiches_urls.py                 # exporte data/fiches_urls.csv pour les 9 048 fiches
    python scripts/fiches_urls.py 15252251552240364339   # une fiche (cid ou place_id)
"""
import sys
import duckdb

BUS = "data/exports/exports/businesses.parquet"


def maps_cid(cid: str) -> str:
    """Ouvre directement la fiche. Le lien le plus fiable."""
    return f"https://www.google.com/maps?cid={cid}"


def maps_place_id(place_id: str) -> str:
    """Ouvre la fiche via le place_id, sans cle API."""
    return f"https://www.google.com/maps/place/?q=place_id:{place_id}"


def cid_hex(cid: str) -> str:
    """Le cid tel qu'il apparait dans les URL longues de Maps (bloc !1s0x...:0x...)."""
    return f"0x{int(cid):x}"


def main() -> None:
    c = duckdb.connect()
    if len(sys.argv) > 1:
        key = sys.argv[1]
        row = c.sql(
            f"SELECT * FROM '{BUS}' WHERE cid = ? OR place_id = ?", params=[key, key]
        ).fetchone()
        if row is None:
            print(f"Aucune fiche pour {key}")
            return
        cols = [d[0] for d in c.sql(f"SELECT * FROM '{BUS}' LIMIT 0").description]
        b = dict(zip(cols, row))
        for k, v in b.items():
            print(f"{k:24} {v}")
        print(f"{'url_cid':24} {maps_cid(b['cid'])}")
        print(f"{'url_place_id':24} {maps_place_id(b['place_id'])}")
        print(f"{'cid_hex':24} {cid_hex(b['cid'])}")
        return

    c.sql(
        f"""
        COPY (
            SELECT name, country, industry, bucket, review_count_at_build,
                   cid, place_id,
                   'https://www.google.com/maps?cid=' || cid AS url_cid,
                   'https://www.google.com/maps/place/?q=place_id:' || place_id AS url_place_id
            FROM '{BUS}'
            ORDER BY name
        ) TO 'data/fiches_urls.csv' (HEADER, DELIMITER ',')
        """
    )
    print("Ecrit : data/fiches_urls.csv")


if __name__ == "__main__":
    main()
