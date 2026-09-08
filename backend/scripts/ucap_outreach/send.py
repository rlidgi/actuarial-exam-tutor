"""One-off outreach send: emails professor_name/university contacts from
contacts.csv with the flyer PDF attached. Not part of the deployed app --
lives here (backend/scripts/, never copied into the Docker image per
Dockerfile) purely so the scheduled GitHub Actions workflow
(.github/workflows/ucap-outreach.yml) can check it out and run it in the
cloud, since it needs to fire at a specific time regardless of whether
anyone's computer is on.

Usage:
    python send.py --test                          # one preview email to admin@resumaticai.com
    python send.py --live --start-row 2 --end-row 278   # real send, inclusive spreadsheet rows (header=row 1)

Reads SMTP_HOST/PORT/USERNAME/PASSWORD from the environment (set as repo
secrets in CI); falls back to backend/.env for local runs.
"""
import argparse
import csv
import os
import smtplib
import time
from email.message import EmailMessage
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV_PATH = HERE.parent.parent / ".env"
CSV_PATH = HERE / "contacts.csv"
FLYER_PATH = HERE / "flyer.pdf"
TEMPLATE_PATH = HERE / "template.html"
LOGO_URL = "https://actuarialexamstutor.com/logo.png"
TEST_RECIPIENT = "admin@resumaticai.com"
SUBJECT = "Actuarial Exams Tutor -- a resource for your actuarial students"


def load_smtp_config():
    host = os.environ.get("SMTP_HOST")
    port = os.environ.get("SMTP_PORT")
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    if password:
        return host, int(port), username, password

    # Local fallback: read backend/.env directly (same file email_service.py's
    # config reads from), so this script works unchanged on a dev machine.
    env = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env["SMTP_HOST"], int(env["SMTP_PORT"]), env["SMTP_USERNAME"], env["SMTP_PASSWORD"]


def load_target_rows(start_row: int, end_row: int):
    """start_row/end_row are 1-indexed spreadsheet row numbers, header = row 1,
    so the first data row is row 2. Inclusive on both ends."""
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    lo = max(0, start_row - 2)
    hi = end_row - 1
    return rows[lo:hi]


def build_message(username: str, to_addr: str, university: str, professor_name: str) -> EmailMessage:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = (
        template.replace("[professor_name]", professor_name)
        .replace("[University]", university)
        .replace("[university]", university)
        .replace("LOGO_URL", LOGO_URL)
    )
    message = EmailMessage()
    message["Subject"] = SUBJECT
    message["From"] = username
    message["To"] = to_addr
    message.set_content(f"Hi {professor_name},\n\n(HTML version has full formatting -- please view in an HTML-capable client.)")
    message.add_alternative(html, subtype="html")
    message.add_attachment(
        FLYER_PATH.read_bytes(), maintype="application", subtype="pdf", filename=FLYER_PATH.name
    )
    return message


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", action="store_true", help="send one preview email to admin@resumaticai.com")
    group.add_argument("--live", action="store_true", help="send to all real target contacts")
    parser.add_argument("--start-row", type=int, default=2, help="spreadsheet row (header=1), inclusive")
    parser.add_argument("--end-row", type=int, default=278, help="spreadsheet row (header=1), inclusive")
    args = parser.parse_args()

    host, port, username, password = load_smtp_config()
    target_rows = load_target_rows(args.start_row, args.end_row)
    print(f"Target rows (spreadsheet rows {args.start_row}-{args.end_row}): {len(target_rows)}")

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(username, password)

        if args.test:
            first = target_rows[0]
            print(f"Sending TEST email to {TEST_RECIPIENT}, using data from: "
                  f"{first['university']} / {first['professor_name']}")
            msg = build_message(username, TEST_RECIPIENT, first["university"], first["professor_name"])
            server.send_message(msg)
            print("Test email sent.")
            return

        sent, failed = [], []
        for i, row in enumerate(target_rows, start=1):
            university = row["university"].strip()
            professor_name = row["professor_name"].strip()
            to_addr = row["email"].strip()
            try:
                msg = build_message(username, to_addr, university, professor_name)
                server.send_message(msg)
                sent.append(to_addr)
                print(f"[{i}/{len(target_rows)}] sent -> {to_addr} ({university})")
            except Exception as exc:
                failed.append((to_addr, str(exc)))
                print(f"[{i}/{len(target_rows)}] FAILED -> {to_addr}: {exc}")
            time.sleep(1.0)

        print()
        print(f"Sent: {len(sent)}/{len(target_rows)}")
        if failed:
            print(f"Failed: {len(failed)}")
            for addr, err in failed:
                print(f"  {addr}: {err}")


if __name__ == "__main__":
    main()
