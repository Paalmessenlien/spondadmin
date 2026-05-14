# GitHub Actions

Two workflows:

- **`ci.yml`** — Frontend build + backend import/alembic check. Runs on every PR and every push to `main` / `production`.
- **`deploy.yml`** — Push to `production` → re-run CI → SSH to server → run `scripts/deploy.sh` → poll `/health`.

## One-time setup

### 1. Repo secrets

GitHub → Settings → Secrets and variables → Actions → **New repository secret**:

| Secret | Value |
| --- | --- |
| `SSH_HOST` | Production server IP or hostname (e.g. `46.224.47.28`) |
| `SSH_USER` | Login user (`deploy`). Must be in the `docker` group |
| `SSH_PRIVATE_KEY` | Contents of the private key paired with the `deploy` user's `~/.ssh/authorized_keys` entry |
| `SSH_KNOWN_HOSTS` | Output of `ssh-keyscan -H <SSH_HOST>`. Pins the server's host key — rotate this when the server is rebuilt |

### 2. Repo variable (optional)

GitHub → Settings → Secrets and variables → Actions → **Variables** tab → **New repository variable**:

| Variable | Default | When to set |
| --- | --- | --- |
| `PROJECT_DIR` | `/srv/app` | If the repo lives somewhere other than `/srv/app` on the server |

### 3. Server architecture

The production server runs:

- **Caddy** on the host — handles TLS termination, HTTP→HTTPS redirect, and `reverse_proxy` to the app containers.
- **Docker Compose** stack inside `/srv/app` — `db` (PostgreSQL), `backend` (FastAPI on `127.0.0.1:8001`), `frontend` (Nuxt on `127.0.0.1:3000`). Both app ports bind to loopback only; UFW also blocks them from the outside.

Caddy expects a config like [`caddy/Caddyfile.example`](../../caddy/Caddyfile.example). Copy it to `/etc/caddy/Caddyfile`, swap in the production domain, then `systemctl reload caddy`. Caddy auto-provisions the TLS cert as soon as the domain's A record points at the server.

### 4. First-time server prep

The first deploy is still manual. On the box as the `deploy` user:

```bash
cd /srv/app
git clone git@github.com:Paalmessenlien/spondadmin.git .
git checkout production
cp .env.production.example .env   # then fill in real values
./scripts/deploy.sh                # first run, manually
```

If you have a database dump (`backups/spondadmin_deploy_*.dump`), restore it after the first build:

```bash
./scripts/restore.sh backups/<file>.dump
```

Once the manual deploy is green, future pushes to `production` deploy automatically.

### 5. Promote `main` → `production`

Day-to-day, push to `main`. CI runs on every push. When you're ready to ship:

```bash
git checkout production
git merge --ff-only main
git push origin production
```

That's the only event that triggers `deploy.yml`. A failing CI on `production` blocks the SSH step entirely.

## Secrets that *don't* live in GitHub

`DATABASE_URL`, `POSTGRES_PASSWORD`, `SPOND_USERNAME`, `SPOND_PASSWORD`, `BUNNY_STORAGE_API_KEY`, AI provider keys, and the bcrypt-hashed admin password all live in `/srv/app/.env` (and `/srv/app/backend/.env`) on the server. They are intentionally **not** in GitHub Actions so a compromised workflow token can't exfiltrate them.

## Rotating the SSH host key

If the server is rebuilt or its host key changes, the deploy job will fail with `Host key verification failed`. From a trusted machine:

```bash
ssh-keyscan -H 46.224.47.28
```

Paste the output as the new `SSH_KNOWN_HOSTS` secret value.
