"""
SCRAPE — Prospection Saint-Étienne (immo + notaires)
-----------------------------------------------------
Lance les deux scrapers en mode complet et écrit les exports dans exports/.
Le filtre "ville de Saint-Étienne" est appliqué APRÈS, par build_master.py.

Env : SE_TEST=true  -> volumes réduits (pour tester vite).
Usage : python scrape.py  &&  python build_master.py
"""

import os
from datetime import datetime, timezone

from scrapers import REGISTRY


def _bool(name: str) -> bool:
    return (os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    test_mode = _bool("SE_TEST")
    print(f"\nScrape Saint-Étienne - test_mode={test_mode} - {datetime.now(timezone.utc).isoformat()}\n")
    exit_code = 0
    for vertical in ("notaires", "immo"):
        print(f"{'='*64}\n> {vertical}\n{'='*64}")
        try:
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
