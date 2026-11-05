# Troubleshooting

Start with `python manage.py check`. It tells you which account the app uses and whether it can reach PostgreSQL.

| Problem | Likely cause and fix |
|---|---|
| `python` is not recognized | Python is not on PATH. Reinstall it and check **Add python.exe to PATH**, or try `py` instead of `python`. Restart the terminal afterwards. |
| `venv\Scripts\activate` is blocked in PowerShell | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use Command Prompt instead. |
| `can't open file 'manage.py'` | You are in the wrong folder. Use `cd` until `dir` lists `manage.py` (a ZIP often extracts into a folder inside a folder). |
| `ModuleNotFoundError: flask` (or `psycopg2`, `dotenv`) | The virtual environment is not active or packages are not installed. Activate it (`venv\Scripts\activate`), then `pip install -r requirements.txt`. In VS Code, press Ctrl+Shift+P, choose **Python: Select Interpreter**, and pick the one inside `venv`. |
| `pip install psycopg2-binary` fails | Upgrade pip (`python -m pip install --upgrade pip`) and use a current Python (3.10 to 3.13). Do not install `psycopg2` (without `-binary`) unless you have a compiler. |
| `Connection refused` / `could not connect to server` | PostgreSQL is not running. Open **Services**, start the `postgresql` service, and check `DB_HOST` and `DB_PORT` in `.env`. |
| `password authentication failed for user "postgres"` during `setup-roles` | The superuser password you typed is wrong. It must be the password set when PostgreSQL was installed. |
| `password authentication failed for user "reserveit_app"` (or `reserveit_owner`) | Run `python manage.py setup-roles` first, and make sure the passwords in `.env` have not changed since then. Running `setup-roles` again resets the passwords to match `.env`. |
| `Add these lines to your .env file first` | `.env` is missing `DB_OWNER_PASSWORD`, `DB_PASSWORD`, `DB_REPORT_PASSWORD`, or `DB_DBA_PASSWORD`. Copy them from `.env.example`. |
| `database "ReserveIT" does not exist` | Create it first in pgAdmin (as `postgres`), or change `DB_NAME` in `.env` to match your database exactly. Capital letters count. |
| `.env` changes are ignored | The file must be named exactly `.env` (not `.env.txt`) and sit next to `manage.py`. Restart the app after editing. |
| `could not open extension control file ... btree_gist` | The contrib modules are missing. Re-run the PostgreSQL installer and include them, or on Linux install `postgresql-contrib`. |
| `permission denied to create extension "btree_gist"` | `setup-roles` has not been run, so the tables are being created by an account that does not own the database. Run `python manage.py setup-roles`. |
| `permission denied for schema public` | The app or owner account lacks schema access. Run `python manage.py grants`. |
| `permission denied for table ...` | A table was added or rebuilt without privileges. Run `python manage.py grants`. |
| `must be owner of table ...` | The structure can only be changed by `reserveit_owner`. Use `init-db` or `reset-db`, not the app account. |
| `relation "department" already exists` | Tables already exist. Use `python manage.py reset-db` to start over (this deletes all data). |
| `duplicate key value violates unique constraint` when seeding | `seed` was run twice. Use `reset-db`, or skip seeding. |
| `column "password_hash" does not exist` at login | The database still has old tables from an earlier version. Run `python manage.py setup-roles` (if you have not), then `python manage.py reset-db` and type `YES`. |
| `reset-db` fails with a permission error | The owner account is missing. Run `python manage.py setup-roles` first, then `reset-db`. |
| `WARNING: this account is a PostgreSQL superuser` | `.env` has `DB_USER=postgres`. Set `DB_USER=reserveit_app` and `DB_PASSWORD` to the app password. |
| `SELECT * FROM app_user` is refused for the reporter account | Expected. That account cannot see email or password columns. Name the columns, for example `SELECT user_id, first_name, last_name FROM app_user`. |
| Login says "Email or password is incorrect" | Sample accounts exist only after `python manage.py seed`. Their password is `ChangeMe123!`. |
| "This form has expired" | The session cookie was lost (for example the server restarted with a new `SECRET_KEY`). Refresh the page and try again. |
| Port 5000 already in use | Close the other program, or run `flask --app app:create_app run --port 5001`. |
| `psql` is not recognized | Add `C:\Program Files\PostgreSQL\18\bin` to PATH, or use pgAdmin. `manage.py` does not need `psql`. |

## Checking what is in the database

```
python tests/access_test.py          # confirms each account's privileges
psql -U reserveit_dba -d ReserveIT   # then:  \dt  to list tables
```

If the problem is not listed, copy the full error message and ask the group that owns the project.
