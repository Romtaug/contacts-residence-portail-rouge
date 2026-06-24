"""
emailing/message.py — contenu des emails (modifiable ici, sans toucher au code).
"""

# --- Mail envoyé aux 25 contacts (texte unique, identique pour tous) ---------

SUBJECT = "Recherche d'achat – résidence Le Portail Rouge (Saint-Étienne)"

# Texte EXACT fourni par Romain. Pas de personnalisation : même mail pour tous.
BODY = """\
Bonjour,

Je me permets de vous contacter en tant qu'acheteur pour un investissement locatif sur Saint-Étienne.

Je suis particulièrement intéressé par la résidence Le Portail Rouge (118 rue Crozet Boussingault, bâtiments Séquoïa, Érable, Sycomore, Sophora, Épicéa), dont vous êtes le syndic. J'apprécie beaucoup le cadre et l'environnement de cette copropriété, et c'est le secteur que je vise en priorité.

Mes critères :
- Type : studio ou T2
- Budget : jusqu'à 60 000 €
- État : clé en main, sans travaux à prévoir
- DPE : A à E (pas de passoire énergétique)
- Étage : à partir du 1er (pas de rez-de-chaussée), un étage élevé avec vue est un plus
- Balcon apprécié
- Bien loué ou immédiatement louable, en meublé de préférence

Mon profil :
- Achat au comptant, sans condition suspensive de prêt
- Prêt à me positionner et signer rapidement

Seriez-vous en mesure de me proposer des biens à la vente dans cette résidence, ou de me prévenir en priorité lorsqu'un lot s'y libère ?

Vous pouvez m'écrire au 07 82 74 00 58 et par mail. Je vous remercie par avance.

Bien cordialement,
Romain Taugourdeau"""


def build_body(vertical: str = "") -> str:
    """Même texte pour tout le monde (agences comme notaires)."""
    return BODY


# --- Mes liens de recherche (récap envoyé à moi-même) ------------------------

SEARCH_LINKS = [
    ("Leboncoin – résidence Portail Rouge (≤60k, appart, DPE A-E)",
     "https://www.leboncoin.fr/recherche?category=9&text=r%C3%A9sidence+portail+rouge"
     "&locations=bbox_4.443669319152833%7C45.43342468070221%7C4.397921562194825%7C45.409146521811195"
     "&price=min-60000&energy_rate=b%2Ca%2Cc%2Cd%2Ce&real_estate_type=2&owner_type=all"
     "&sort=price&order=asc&kst=k"),
    ("SeLoger – La Métare / Le Portail Rouge 42100 (≤60k, appart meublé, DPE A-E)",
     "https://www.seloger.com/classified-search?distributionTypes=Buy"
     "&energyCertificate=A,B,C,D,E&estateTypes=Apartment&furnished=Full"
     "&locations=NBH2FR9405&priceMax=60000"),
]

RECAP_SUBJECT = "[Récap] Mes recherches d'achat en cours – Saint-Étienne"


def build_recap_body(n_contacts: int) -> str:
    links = "\n\n".join(f"• {label}\n{url}" for label, url in SEARCH_LINKS)
    return (
        "Récap de la campagne de prospection achat (Saint-Étienne).\n\n"
        f"Mail envoyé à {n_contacts} contacts (agences + notaires).\n\n"
        "Mes liens de recherche enregistrés :\n\n"
        f"{links}\n\n"
        "Critères : studio/T2, ≤ 60 000 €, clé en main, DPE A-E, "
        "résidence Le Portail Rouge.\n"
    )
