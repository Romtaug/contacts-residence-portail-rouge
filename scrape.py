"""
SCRAPE — Prospection Saint-Étienne (immo + notaires)
-----------------------------------------------------
Lance les scrapers et écrit les exports dans exports/.
Le filtre "ville de Saint-Étienne" est appliqué APRÈS, par build_master.py.

Variables d'environnement (utilisées par le workflow GitHub Actions) :
  CIBLE          = notaires | immo | les_deux   (défaut : les_deux)
  IMMO_MAX_PAGES = nombre max de pages immomatin (évite un crawl national sans fin)
  SE_TEST        = true  -> volumes réduits (test rapide)

Usage local : python scrape.py  &&  python build_master.py
"""

import os
from datetime import datetime, timezone

from scrapers import REGISTRY


def _bool(name: str) -> bool:
    return (os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default=None):
    v = (os.getenv(name) or "").strip()
    return int(v) if v.lstrip("-").isdigit() else default


def main() -> int:
    test_mode = _bool("SE_TEST")
    cible = (os.getenv("CIBLE") or "").strip().lower()
    immo_max = _int("IMMO_MAX_PAGES", None)

    if cible in ("", "les_deux", "both", "tout"):
        verticals = ["notaires", "immo"]
    elif cible in REGISTRY:
        verticals = [cible]
    else:
        print(f"CIBLE inconnue : {cible!r} (attendu : notaires | immo | les_deux)")
        return 1

    print(f"\nScrape Saint-Étienne - cibles={verticals} - test={test_mode} "
          f"- immo_max_pages={immo_max} - {datetime.now(timezone.utc).isoformat()}\n")

    exit_code = 0
    for vertical in verticals:
        print(f"{'='*64}\n> {vertical}\n{'='*64}")
        try:
            if vertical == "immo":
                scraper = REGISTRY["immo"](test_mode=test_mode, max_pages=immo_max)
            else:
                scraper = REGISTRY[vertical](test_mode=test_mode)
            res = scraper.run(mode="update")
            print(f"OK {vertical} : +{res.inserted} / maj {res.updated} / = {res.unchanged}")
        except Exception as exc:
            exit_code = 1
            print(f"ERREUR {vertical} : {exc!r}")

    print("\n-> Ensuite : python build_master.py")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
