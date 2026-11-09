"""Print a secrets line for a new DiMEx account (the password is hashed, never stored as typed).

    python scripts/add_user.py name@unf.edu

Paste the printed line under [users] in Streamlit Cloud's App settings -> Secrets
(or .streamlit/secrets.toml locally), then share the password with that person privately.
"""
import getpass
import sys

import bcrypt

email = (sys.argv[1] if len(sys.argv) > 1 else input("Email: ")).strip().lower()
pw = getpass.getpass("Password (min 10 characters): ")
if len(pw) < 10 or pw != getpass.getpass("Repeat password: "):
    sys.exit("Passwords must match and be at least 10 characters.")
print(f'"{email}" = "{bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()}"')
