"""
BUILD MASTER — Prospection Saint-Étienne
----------------------------------------
Fusionne en UNE seule table, automatiquement et sans doublon :

  1. seed/seed_contacts.csv          -> les emails que TU as fournis à la main
  2. exports/notaires/...loire.csv   -> notaires scrapés (notaires.fr)
  3. exports/immo/agences_immo.csv   -> agences scrapées (immomatin.com)

Filtre géographique : VILLE DE SAINT-ÉTIENNE uniquement (nom + code postal 42).
La seed list n'est PAS filtrée (tu l'as choisie à la main, on garde tout).

Le suivi d'envoi (send_status, sent_at, ...) est préservé entre deux runs :
relancer le scraper n'efface jamais ce qui a déjà été envoyé.

Sorties :
  master/contacts_master.csv   (UTF-8 BOM, compatible Excel)
  master/contacts_master.xlsx  (table stylée)

Usage : python build_master.py
"""

import csv
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

# core.export fournit le bel export XLSX (réutilisé tel quel)
try:
    from core.export import export_xlsx
except Exception:
    export_xlsx = None

BASE_DIR = Path(__file__).resolve().parent
EXPORTS_DIR = BASE_DIR / "exports"
SEED_PATH = BASE_DIR / "seed" / "seed_contacts.csv"
MASTER_CSV = BASE_DIR / "master" / "contacts_master.csv"
MASTER_XLSX = BASE_DIR / "master" / "contacts_master.xlsx"


# ---------------------------------------------------------------------------
# Filtre géographique : ville de Saint-Étienne (42)
# ---------------------------------------------------------------------------

CP_42 = re.compile(r"\b42\d{3}\b")


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def _norm(s) -> str:
    return _strip_accents(("" if s is None else str(s))).strip().lower()


# Le nom doit être COLLÉ à un code postal de Saint-Étienne (= la commune),
# pas juste apparaître dans une adresse type "rue de Saint-Étienne" d'une
# autre ville (ex : Saint-Chamond 42400, Balbigny 42510).
_SE_CP = r"(?:4200\d|4201\d|4202\d|4203\d|4205\d|42100|42230|4295\d)"
_NAME = r"(?:saint[- ]etienne|st[-. ]?etienne)"
_SE_PATTERNS = (
    re.compile(_NAME + r"\s*\(\s*" + _SE_CP),         # "saint-etienne (42000)"
    re.compile(r"\b" + _SE_CP + r"\b\s+" + _NAME + r"\b"),  # "42000 saint-etienne"
    re.compile(_NAME + r"\s+" + _SE_CP + r"\b"),       # "saint-etienne 42000"
)


def is_saint_etienne(text: str) -> bool:
    """
    True seulement si le texte désigne la VILLE de Saint-Étienne (42), avec le
    nom de commune directement associé à un code postal stéphanois.
    -> exclut les communes voisines, les homonymes (Saint-Étienne-de-Montluc)
       et les adresses qui ne font que citer une "rue de Saint-Étienne" ailleurs.
    """
    t = _norm(text)
    if "saint-etienne-de" in t or "st-etienne-de" in t:
        return False  # Saint-Étienne-de-Montluc / -du-Rouvray / etc.
    return any(p.search(t) for p in _SE_PATTERNS)


def _geo_notaire(row: dict) -> bool:
    # Le champ 'city' de notaires.fr est fiable : on tranche dessus en priorité.
    city = _norm(row.get("city"))
    if city:
        return city == "saint-etienne"
    # Pas de ville renseignée -> repli sur l'adresse / le nom d'office.
    blob = " ".join(_norm(row.get(c)) for c in ("address", "office", "department"))
    return is_saint_etienne(blob)


def _geo_immo(row: dict) -> bool:
    blob = " ".join(_norm(row.get(c)) for c in ("adresse", "nom", "description"))
    return is_saint_etienne(blob)


# ---------------------------------------------------------------------------
# Sources
# (vertical, fichier, col_email, cols_extra, col_company, col_city, col_phone, rank, filtre_geo)
# rank élevé = source prioritaire en cas de doublon d'email.
# ---------------------------------------------------------------------------

SOURCES = [
    ("notaires", "notaires/annuaire_notaires_loire.csv",
     "email", ["emails_all"], "office", "city", "phone", 6, _geo_notaire),
    ("immo", "immo/agences_immo.csv",
     "email_principal", ["emails_trouves"], "nom", None, "telephone_principal", 5, _geo_immo),
]

FIELDNAMES = [
    "email", "vertical", "company", "city", "phone", "score_source_rank",
    "email_sent", "sent_at", "send_status", "send_attempts",
    "last_error", "last_subject", "created_at", "updated_at",
]
TRACKING_FIELDS = [
    "email_sent", "sent_at", "send_status", "send_attempts",
    "last_error", "last_subject", "created_at",
]

_EMAIL_SPLIT = re.compile(r"[;,|\s]+")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(v) -> str:
    return "" if v is None else str(v).strip()


def _valid_email(e: str) -> bool:
    return bool(e and "@" in e and "." in e.split("@")[-1]
                and " " not in e and len(e) <= 254)


def _emails_from(value) -> list[str]:
    out: list[str] = []
    for tok in _EMAIL_SPLIT.split(_clean(value).lower()):
        tok = tok.strip(" ;,|")
        if _valid_email(tok) and tok not in out:
            out.append(tok)
    return out


# ---------------------------------------------------------------------------
# Collecte
# ---------------------------------------------------------------------------

def collect_from_seed(prospects: dict[str, dict]) -> None:
    """La seed = emails fournis à la main. Rank max, jamais filtrée, jamais écrasée."""
    if not SEED_PATH.exists():
        print(f"!! seed absente ({SEED_PATH.name}) - ignore")
        return
    n = 0
    with SEED_PATH.open("r", newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            for email in _emails_from(row.get("email")):
                prospects[email] = {
                    "email": email,
                    "vertical": _clean(row.get("vertical")) or "immo",
                    "company": _clean(row.get("company")),
                    "city": _clean(row.get("city")) or "Saint-Étienne",
                    "phone": _clean(row.get("phone")),
                    "score_source_rank": "10",
                }
                n += 1
    print(f"[{'seed':<10}] {n:>4} emails fournis à la main (rank 10, non filtrés)")


def collect_from_scrapers(prospects: dict[str, dict]) -> None:
    for vertical, rel, col_email, cols_extra, col_company, col_city, col_phone, rank, geo in SOURCES:
        path = EXPORTS_DIR / rel
        if not path.exists():
            print(f"!! {vertical:<10} : export absent ({rel}) - lance le scraper d'abord")
            continue
        n_rows = n_geo = n_kept = 0
        with path.open("r", newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                n_rows += 1
                if not geo(row):
                    continue
                n_geo += 1
                emails = _emails_from(row.get(col_email))
                for c in cols_extra:
                    for e in _emails_from(row.get(c)):
                        if e not in emails:
                            emails.append(e)
                for email in emails:
                    existing = prospects.get(email)
                    if existing and int(existing["score_source_rank"]) >= rank:
                        continue  # déjà vu via une source plus prioritaire (seed/notaires)
                    prospects[email] = {
                        "email": email,
                        "vertical": vertical,
                        "company": _clean(row.get(col_company)) if col_company else "",
                        "city": _clean(row.get(col_city)) if col_city else "Saint-Étienne",
                        "phone": _clean(row.get(col_phone)) if col_phone else "",
                        "score_source_rank": str(rank),
                    }
                    n_kept += 1
        print(f"[{vertical:<10}] {n_rows:>4} lignes -> {n_geo:>4} à Saint-Étienne -> {n_kept:>4} emails")


def load_existing_master() -> dict[str, dict]:
    if not MASTER_CSV.exists():
        return {}
    out: dict[str, dict] = {}
    with MASTER_CSV.open("r", newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            email = _clean(row.get("email")).lower()
            if email:
                out[email] = row
    return out


def main() -> int:
    print(f"\nBuild master Saint-Étienne - {_now()}\n")

    prospects: dict[str, dict] = {}
    collect_from_seed(prospects)        # 1. tes emails
    collect_from_scrapers(prospects)    # 2. + 3. scraping (filtré SE)

    if not prospects:
        print("\nAucun prospect - seed vide ET exports manquants/vides ?")
        return 1

    existing = load_existing_master()
    now = _now()
    n_new = n_kept_tracking = 0
    merged: list[dict] = []

    for email, p in prospects.items():
        row = {f: "" for f in FIELDNAMES}
        row.update(p)
        old = existing.get(email)
        if old:
            for f in TRACKING_FIELDS:
                row[f] = _clean(old.get(f))
            if _clean(old.get("send_status")):
                n_kept_tracking += 1
        if not row["send_status"]:
            row["send_status"] = "pending"
            row["email_sent"] = "false"
            row["send_attempts"] = "0"
            row["created_at"] = now
            n_new += 1
        row["updated_at"] = now
        merged.append(row)

    # On garde les anciens contacts qui ont disparu des sources (historique/tracking)
    n_orphans = 0
    for email, old in existing.items():
        if email not in prospects:
            row = {f: _clean(old.get(f)) for f in FIELDNAMES}
            row["email"] = email
            merged.append(row)
            n_orphans += 1

    merged.sort(key=lambda r: (-int(r.get("score_source_rank") or 0), r["email"]))

    MASTER_CSV.parent.mkdir(parents=True, exist_ok=True)
    with MASTER_CSV.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDNAMES, extrasaction="ignore")
        w.writeheader()
        w.writerows(merged)

    # Export XLSX stylé (même moteur que les exports par vertical)
    if export_xlsx is not None:
        try:
            export_xlsx(
                merged, FIELDNAMES, MASTER_XLSX,
                sheet_name="Contacts", table_name="ContactsMaster",
                email_column="email",
                summary=[
                    ("Périmètre", "Ville de Saint-Étienne (42)"),
                    ("Total contacts", len(merged)),
                    ("Build", now),
                ],
            )
        except Exception as exc:
            print(f"(XLSX non généré : {exc!r})")

    n_pending = sum(1 for r in merged if r["send_status"] == "pending")
    n_sent = sum(1 for r in merged if r["send_status"] == "sent")
    by_vertical = {}
    for r in merged:
        by_vertical[r["vertical"]] = by_vertical.get(r["vertical"], 0) + 1

    print(f"\nMaster écrit : {len(merged)} contacts (Saint-Étienne)")
    print(f"  par vertical      : {by_vertical}")
    print(f"  nouveaux pending  : {n_new}")
    print(f"  tracking préservé : {n_kept_tracking}")
    print(f"  orphelins gardés  : {n_orphans}")
    print(f"  état              : {n_pending} pending / {n_sent} sent")
    print(f"\n  -> {MASTER_CSV}")
    if export_xlsx is not None:
        print(f"  -> {MASTER_XLSX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
