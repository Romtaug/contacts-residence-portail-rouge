"""
emailing/send.py — Envoi des mails (Gmail SMTP, mot de passe d'application)
===========================================================================

3 niveaux, du plus sûr au plus engageant :

  python emailing/send.py --dry-run     # n'envoie RIEN : affiche les mails (aucun
                                         # identifiant requis). Pour vérifier le contenu.
  python emailing/send.py               # MODE TEST : envoie tout sur TON adresse
                                         # (rien aux vrais contacts). Identifiants requis.
  python emailing/send.py --real        # ENVOI RÉEL aux agences + notaires.

Options : --no-recap (ne pas s'envoyer le récap de liens) | --limit N

Identifiants (fichier .env à la racine, voir .env.example) :
  GMAIL_ADDRESS=ton.adresse@gmail.com
  GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx   # mot de passe d'application Google (16 lettres)
"""

from __future__ import annotations

import argparse
import csv
import os
import smtplib
import sys
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

# import du contenu (sujet, corps, liens)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import message as msg  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
MASTER_CSV = BASE_DIR / "master" / "contacts_master.csv"
ENV_PATH = BASE_DIR / ".env"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
FROM_NAME = "Romain Taugourdeau"
SLEEP_BETWEEN = 1.5          # secondes entre 2 envois (rester poli)
DAILY_CAP = 80               # garde-fou (Gmail ~500/j en pratique)

FIELDNAMES = [
    "email", "vertical", "company", "city", "phone", "score_source_rank",
    "email_sent", "sent_at", "send_status", "send_attempts",
    "last_error", "last_subject", "created_at", "updated_at",
]


# ---------------------------------------------------------------------------

def load_env() -> None:
    """Charge .env (KISS, sans dépendance) dans os.environ s'il existe."""
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_master() -> list[dict]:
    if not MASTER_CSV.exists():
        print(f"!! master introuvable : {MASTER_CSV}")
        print("   Lance d'abord : python build_master.py")
        sys.exit(1)
    with MASTER_CSV.open("r", newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def write_master(rows: list[dict]) -> None:
    with MASTER_CSV.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDNAMES, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({f: r.get(f, "") for f in FIELDNAMES})


def build_email(from_addr: str, to_addr: str, subject: str, body: str) -> EmailMessage:
    em = EmailMessage()
    em["From"] = formataddr((FROM_NAME, from_addr))
    em["To"] = to_addr
    em["Reply-To"] = from_addr
    em["Subject"] = subject
    em.set_content(body)
    return em


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true", help="envoi réel aux vrais contacts")
    ap.add_argument("--dry-run", action="store_true", help="n'envoie rien, affiche les mails")
    ap.add_argument("--no-recap", action="store_true", help="ne pas s'envoyer le récap de liens")
    ap.add_argument("--resend-all", action="store_true",
                    help="renvoyer à TOUT le monde, même aux contacts déjà 'sent' (relance)")
    ap.add_argument("--limit", type=int, default=None, help="limiter le nombre d'envois")
    args = ap.parse_args()

    load_env()
    gmail = os.environ.get("GMAIL_ADDRESS", "").strip()
    app_pwd = os.environ.get("GMAIL_APP_PASSWORD", "").strip()

    if args.dry_run:
        mode = "DRY-RUN"
    elif args.real:
        mode = "RÉEL"
    else:
        mode = "TEST"

    print(f"\n=== Envoi mails — mode {mode} ===\n")

    # Vérif des identifiants (sauf dry-run)
    from_addr = gmail or "moi@exemple.com"
    if mode != "DRY-RUN":
        if not gmail or not app_pwd:
            print("!! GMAIL_ADDRESS / GMAIL_APP_PASSWORD manquants.")
            print("   Crée un fichier .env (voir .env.example) avec ton Gmail + mot de passe d'application.")
            return 1

    rows = read_master()
    if args.resend_all:
        pending = list(rows)            # relance : on renvoie à tout le monde
    else:
        pending = [r for r in rows if (r.get("send_status") or "").strip() != "sent"]
    if args.limit:
        pending = pending[: args.limit]

    if not pending:
        print("Aucun contact 'pending' — tout a déjà été envoyé.")
    else:
        print(f"{len(pending)} contact(s) à traiter "
              f"(cap quotidien {DAILY_CAP}).\n")

    # Connexion SMTP (test + réel)
    server = None
    if mode != "DRY-RUN":
        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
            server.starttls()
            server.login(gmail, app_pwd)
        except Exception as exc:
            print(f"!! Connexion Gmail impossible : {exc!r}")
            return 1

    sent = 0
    for r in pending:
        if sent >= DAILY_CAP:
            print(f"\n[STOP] cap quotidien atteint ({DAILY_CAP}).")
            break

        real_to = (r.get("email") or "").strip()
        vertical = (r.get("vertical") or "").strip()
        company = (r.get("company") or "").strip()
        body = msg.build_body(vertical)
        subject = msg.SUBJECT

        # destinataire effectif selon le mode
        if mode == "RÉEL":
            to_addr, sub = real_to, subject
        else:  # TEST / DRY-RUN : tout vers soi, on annonce le vrai destinataire
            to_addr = from_addr
            sub = f"[TEST → {real_to}] {subject}"
            body = (f"*** MODE TEST — ce mail serait envoyé à : {real_to} "
                    f"({company} / {vertical}) ***\n\n{body}")

        em = build_email(from_addr, to_addr, sub, body)

        if mode == "DRY-RUN":
            print("-" * 70)
            print(f"From    : {em['From']}")
            print(f"To      : {em['To']}   (réel: {real_to} / {company})")
            print(f"Subject : {em['Subject']}")
            print(em.get_content().rstrip()[:600])
            sent += 1
            continue

        try:
            server.send_message(em)
            sent += 1
            print(f"[OK]   {real_to:<45} ({company})")
            # On ne marque 'sent' QUE en mode réel (le test n'a rien envoyé aux vrais).
            if mode == "RÉEL":
                r["send_status"] = "sent"
                r["email_sent"] = "true"
                r["sent_at"] = now_iso()
                r["send_attempts"] = str(int(r.get("send_attempts") or 0) + 1)
                r["last_subject"] = subject
                r["last_error"] = ""
                r["updated_at"] = now_iso()
            time.sleep(SLEEP_BETWEEN)
        except Exception as exc:
            print(f"[ERR]  {real_to:<45} -> {exc!r}")
            if mode == "RÉEL":
                r["send_status"] = "error"
                r["send_attempts"] = str(int(r.get("send_attempts") or 0) + 1)
                r["last_error"] = repr(exc)[:300]
                r["updated_at"] = now_iso()

    # Récap de mes liens de recherche -> à MOI
    if not args.no_recap:
        recap = build_email(
            from_addr, from_addr,
            msg.RECAP_SUBJECT, msg.build_recap_body(len(pending)),
        )
        if mode == "DRY-RUN":
            print("-" * 70)
            print(f"[RÉCAP → moi] {recap['Subject']}")
            print(recap.get_content().rstrip())
        else:
            try:
                server.send_message(recap)
                print(f"\n[RÉCAP] liens de recherche envoyés à {from_addr}")
            except Exception as exc:
                print(f"\n[RÉCAP] échec : {exc!r}")

    if server is not None:
        server.quit()

    # Sauvegarde du suivi (réel uniquement)
    if mode == "RÉEL":
        write_master(rows)
        print("\nSuivi mis à jour dans master/contacts_master.csv")

    print(f"\nTerminé — mode {mode} — {sent} mail(s) traité(s).")
    if mode == "TEST":
        print("=> Vérifie ta boîte. Si OK, relance avec --real pour les vrais contacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
