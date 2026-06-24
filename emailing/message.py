"""
emailing/message.py — contenu des emails (modifiable ici, sans toucher au code).
"""

# --- Mail envoyé aux agences / notaires --------------------------------------

SUBJECT = (
    "Recherche achat investissement locatif – studio/T2, "
    "secteur Le Portail Rouge / Fauriel (Saint-Étienne)"
)

# Texte exact fourni par Romain. {greeting} permet d'adapter "agence"/"étude".
BODY = """\
Bonjour,

Je suis acheteur pour un investissement locatif sur Saint-Étienne et je me permets de vous transmettre ma recherche, au cas où un bien correspondant passerait par votre {lieu}.

Je vise en priorité la résidence Le Portail Rouge (118 rue Crozet Boussingault), dont j'apprécie particulièrement le cadre, et je reste ouvert au secteur Fauriel / Crêt de Roc.

Mes critères :
- Type : studio ou T2
- Budget : jusqu'à 60 000 € environ, frais inclus
- État : clé en main, sans travaux à prévoir
- DPE : A à E
- Étage : à partir du 1er, un étage élevé avec vue est un plus
- Balcon apprécié
- Bien loué ou immédiatement louable, meublé de préférence

Mon profil : achat au comptant, sans condition suspensive de prêt, prêt à me positionner et signer rapidement.

Seriez-vous en mesure de me proposer des biens correspondants, ou de me prévenir lorsqu'un lot se libère ? Je suis joignable au 07 82 74 00 58 et par mail.

Je vous remercie par avance.

Bien cordialement,
Romain Taugourdeau"""


def build_body(vertical: str) -> str:
    """Adapte 'votre agence' -> 'votre étude' pour les notaires."""
    lieu = "étude" if vertical == "notaires" else "agence"
    return BODY.format(lieu=lieu)


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
        "Critères : studio/T2, ≤ 60 000 € FAI, clé en main, DPE A-E, "
        "secteur Le Portail Rouge / Fauriel / Crêt de Roc.\n"
    )
