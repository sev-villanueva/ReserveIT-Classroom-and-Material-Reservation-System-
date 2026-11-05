# Troubleshooting

Start with `python manage.py check`. It tells you whether Python can reach PostgreSQL.

| Problem | Likely cause and fix |
|---|---|
| `python` is not recognized | Python is not on PATH. Reinstall it and tick **Add python.exe to PATH**, or try `py` instead of `python`. Restart the terminal afterwards. |
| `venv\Scripts\activate` is blocked in PowerShell | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use Command Prompt instead. |
| `ModuleNotFoundError: flask` (or `psycopg2`, `dotenv`) | The virtual environment is not active or packages are not installed. Activate it (`venv\Scripts\activate`), then `pip install -r requirements.txt`. In VS Code, press Ctrl+Shift+P, choose **Python: Select Interpreter**, and pick the one inside `venv`. |
| `pip install psycopg2-binary` fails | Upgrade pip (`python -m pip install --upgrade pip`) and use a current Python (3.10 to 3.13). Do not install `psycopg2` (without `-binary`) unless you have a compiler. |
| `Connection refused` / `could not connect to server` | PostgreSQL is not running. Open **Services**, start `postgresql-x64-18` (or your version), and check `DB_HOST` and `DB_PORT` in `.env`. |
| `password authentication failed for user` | `DB_PASSWORD` in `.env` is wrong for `DB_USER`. Test the same password in pgAdmin or `psql -U postgres`. |
| `database "grp01_appdb" does not exist` | Create it first: `psql -U postgres -c "CREATE DATABASE grp01_appdb;"`, or change `DB_NAME` in `.env` to match yours. |
| `.env` changes are ignored | The file must be named exactly `.env` (not `.env.txt`) and sit in the project root next to `manage.py`. Restart the app after editing. |
| `could not open extension control file ... btree_gist` | The contrib modules are missing. Re-run the PostgreSQL installer and include them, or on Linux install `postgresql-contrib`. |
| `permission denied to create extension "btree_gist"` | Run `init-db` with a superuser such as `postgres`. Only the extension creation needs it. |
| `relation "department" already exists` | Tables are already created. Use `python manage.py reset-db` to start over (this deletes all data). |
| `duplicate key value violates unique constraint` when seeding | `seed` was run twice. Use `reset-db`, or skip seeding. |
| `relation "room" does not exist` when using `reserveit_app` | The roles were created before the tables, or `reset-db` removed the grants. Re-run `roles_setup.sql` (see docs/user-roles.md). |
| `permission denied for table ...` | The login account lacks privileges. Use `postgres` for setup, or run `roles_setup.sql` and use `reserveit_app`. |
| Login says "Email or password is incorrect" | Sample accounts exist only after `python manage.py seed`. Their password is `ChangeMe123!`. |
| "This form has expired" | The session cookie was lost (for example the server restarted with a new `SECRET_KEY`). Refresh the page and try again. |
| Port 5000 already in use | Close the other program, or run `flask --app app:create_app run --port 5001`. |
| `UnicodeDecodeError` when running SQL on Windows | Save SQL files as UTF-8. The provided files already are. |
| `psql` is not recognized | Add `C:\Program Files\PostgreSQL\18\bin` to PATH, or run it by full path. |

## Checking what is in the database

```
psql -U postgres -d grp01_appdb
\dt                                   -- list tables
SELECT * FROM reservation LIMIT 5;
```

If the problem is not listed, copy the full error message and ask the group that owns the project.
