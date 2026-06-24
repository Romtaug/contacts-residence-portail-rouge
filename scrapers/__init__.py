"""
Package scrapers — prospection Saint-Étienne.

Deux cibles : agences immobilières (immomatin.com) et notaires (notaires.fr).
Le périmètre géographique (ville de Saint-Étienne) est appliqué au moment du
build_master, sur l'adresse / le code postal.
"""

from scrapers.immo import ImmoScraper
from scrapers.notaires import NotairesScraper


REGISTRY = {
    "immo": ImmoScraper,
    "notaires": NotairesScraper,
}


__all__ = [
    "REGISTRY",
    "ImmoScraper",
    "NotairesScraper",
]
