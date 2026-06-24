# Prospection Saint-Étienne — agences immo + notaires

Pipeline de prospection **automatique** pour **la ville de Saint-Étienne (42)**.
Il fusionne dans **une seule table dédoublonnée** :

1. **tes emails fournis à la main** (`seed/seed_contacts.csv`) ;
2. les **agences immobilières** scrapées (immomatin.com) ;
3. les **notaires** scrapés (notaires.fr).

Tout finit dans `master/contacts_master.csv` (+ `.xlsx`), avec un suivi d'envoi
(`send_status`, `sent_at`...) **préservé d'un run à l'autre**.

> C'est un nouveau projet, indépendant. Il réutilise le moteur `core/` (SQLite +
> upsert + export) de ton ancien repo, mais reciblé Saint-Étienne.

---

## Structure

```
Prospection-Saint-Etienne/
├── core/                 # moteur réutilisé (DB SQLite, upsert, export CSV/XLSX)
├── scrapers/
│   ├── immo.py           # immomatin.com (annuaire national, filtré SE au build)
│   └── notaires.py       # notaires.fr → Loire / Saint-Étienne
├── seed/
│   ├── seed_contacts.csv # ← TES emails (les 13 agences). Modifiable à la main.
│   └── NOTES_notaires_saint_etienne.md
├── exports/              # sorties brutes des scrapers (1 fichier / vertical)
├── master/
│   ├── contacts_master.csv   # ← LA table finale (dédoublonnée, avec tracking)
│   └── contacts_master.xlsx
├── emailing/
│   ├── send.py           # envoi Gmail (dry-run / test / réel) + récap perso
│   └── message.py        # ← le texte du mail + sujet + tes liens de recherche
├── build_master.py       # fusionne seed + exports → master (filtre SE + dédup)
├── scrape.py             # lance les 2 scrapers
├── .env.example          # → copie en .env et mets ton Gmail + mot de passe d'app
└── requirements.txt
```

## Utilisation

```bash
pip install -r requirements.txt

# 1) récupère agences + notaires (peut être long : immomatin = annuaire national)
python scrape.py            # SE_TEST=true python scrape.py  → version rapide/réduite

# 2) fusionne tout dans la table master (seed + scraping), filtré Saint-Étienne
python build_master.py
```

Tu peux aussi lancer **uniquement `build_master.py`** : il intègre déjà ta seed
list. C'est ce qui a généré le master actuel (13 agences + 3 notaires).

## Envoyer les mails (Gmail)

1. Crée un **mot de passe d'application** Google (validation en 2 étapes requise) :
   https://myaccount.google.com/apppasswords
2. Copie `.env.example` en `.env` et remplis `GMAIL_ADDRESS` + `GMAIL_APP_PASSWORD`.
3. Envoie, du plus sûr au plus engageant :

```bash
python emailing/send.py --dry-run   # n'envoie RIEN, affiche les mails (sans identifiants)
python emailing/send.py             # MODE TEST : tout sur TON adresse (rien aux vrais contacts)
python emailing/send.py --real      # ENVOI RÉEL aux agences + notaires
```

Options : `--no-recap` (ne pas s'envoyer le récap de liens), `--limit N`.

- Le **texte du mail** se modifie dans `emailing/message.py` (le mot « agence »
  devient « étude » pour les notaires, automatiquement).
- À la fin, tu reçois sur ta propre adresse un **récap avec tes liens de recherche**
  (leboncoin + seloger).
- En mode `--real`, chaque contact n'est mailé **qu'une fois** : le suivi
  (`send_status=sent`) est écrit dans le master, donc relancer ne renvoie pas.
- Le mode TEST et le dry-run **ne touchent pas** au suivi (les vrais contacts
  restent `pending`).

## Ce que fait `build_master.py`

- **seed** = priorité max (`rank 10`), **jamais filtrée** (tu l'as choisie) et
  **jamais écrasée** par le scraping.
- **notaires** (`rank 6`) et **immo** (`rank 5`) sont filtrés sur la **ville de
  Saint-Étienne** (nom *Saint-Étienne* **+** code postal `42xxx`). Les communes
  voisines (Saint-Priest-en-Jarez, Roche-la-Molière, Saint-Jean-Bonnefonds…) et
  les homonymes (Saint-Étienne-de-Montluc en 44…) sont **exclus**.
- Dédoublonnage par email ; en cas de doublon, la source la plus prioritaire gagne.
- Le suivi d'envoi des contacts déjà présents est conservé.

## État actuel du master

16 contacts : **13 agences** (ta liste) + **3 notaires** (emails confirmés).
Les ~8 autres offices notariaux de Saint-Étienne (téléphones connus, voir
`seed/NOTES_notaires_saint_etienne.md`) seront ajoutés automatiquement avec leur
email dès que tu lanceras `python scrape.py`.

## Note RGPD

`master/` et `exports/` contiennent des emails de personnes/structures réelles.
Si tu rends le repo public, dé-commente les lignes correspondantes dans
`.gitignore`.
