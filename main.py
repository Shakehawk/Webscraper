from sheets import connect
from scraper import scrape_shop
from config import SHOPS, GOOGLE_SHEET_NAME
from datetime import datetime
import time

print("🚀 Scraper gestartet")

gc = connect()
sh = gc.open(GOOGLE_SHEET_NAME)

overview = sh.worksheet("GESAMTUEBERSICHT")
new_items = sh.worksheet("NEUER_ARTIKEL")

existing = overview.get_all_records()

# eindeutiger Schlüssel: (Name, Shop)
existing_map = {
    (row["Name"].strip().lower(), row["Shop"].strip().lower()): (idx + 2, row)
    for idx, row in enumerate(existing)
}

# stabile Produkt_ID
if existing:
    next_product_id = max(row["Produkt_ID"] for row in existing) + 1
else:
    next_product_id = 1

now = datetime.now().strftime("%Y-%m-%d %H:%M")

rows_to_append = []
new_items_rows = []

for shop in SHOPS:
    products = scrape_shop(shop)

    for p in products:
        key = (p["name"].strip().lower(), p["shop"].strip().lower())

        # PRODUKT EXISTIERT
        if key in existing_map:
            row_index, row = existing_map[key]

            preis_alt = row["Preis_ALT"]
            preis_neu = row["Preis_NEU"]
            last_price = preis_neu if preis_neu else preis_alt

            # Preis unverändert → nichts tun
            if float(last_price) == float(p["price"]):
                continue

            # Preis geändert → NUR Preis_NEU + Datum setzen
            overview.update(f"G{row_index}", [[p["price"]]])
            overview.update(f"J{row_index}", [[now]])
            time.sleep(1)

        # NEUER ARTIKEL
        else:
            rows_to_append.append([
                next_product_id,   # A Produkt_ID
                p["name"],         # B Name
                "Vape",            # C Kategorie
                p["shop"],         # D Shop
                p["url"],          # E URL
                p["price"],        # F Preis_ALT
                "",                # G Preis_NEU
                "",                # H Diff_%
                "",                # I Diff_€
                now                # J Letztes Update
            ])

            new_items_rows.append([
                now,
                p["name"],
                p["shop"],
                p["url"],
                p["price"]
            ])

            existing_map[key] = True
            next_product_id += 1


if rows_to_append:
    overview.append_rows(rows_to_append, value_input_option="USER_ENTERED")

if new_items_rows:
    new_items.append_rows(new_items_rows, value_input_option="USER_ENTERED")
