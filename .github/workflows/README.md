# GitHub Actions

Two workflows:

- **`ci.yml`** — Frontend build + backend import/alembic check. Runs on every PR and every push to `main` / `production`.
- **`deploy.yml`** — Push to `production` → re-run CI → SSH to server → run `scripts/deploy.sh` → poll `/health`.

## One-time setup

### 1. Repo secrets

GitHub → Settings → Secrets and variables → Actions → **New repository secret**:

| Secret | Value |
| --- | --- |
| `SSH_HOST` | Production server IP or hostname, e.g. `admin.lillehammerbueskyttere.no` |
| `SSH_USER` | Login user. Must have access to `PROJECT_DIR` and be in the `docker` group |
| `SSH_PRIVATE_KEY` | Contents of the private key paired with a `~/.ssh/authorized_keys` entry on the server |
| `SSH_KNOWN_HOSTS` | Output of `ssh-keyscan -H <SSH_HOST>` run from a trusted machine. Pins the server's host key |

### 2. Repo variable (optional)

GitHub → Settings → Secrets and variables → Actions → **Variables** tab → **New repository variable**:

| Variable | Default | When to set |
| --- | --- | --- |
| `PROJECT_DIR` | `/opt/spondadmin` | If you cloned the repo somewhere else on the server |

### 3. Server prep

The first deploy is still manual. On the box:

```bash
sudo mkdir -p /opt/spondadmin && sudo chown "$USER:$USER" /opt/spondadmin
git clone git@github.com:Paalmessenlien/spondadmin.git /opt/spondadmin
cd /opt/spondadmin
git checkout production
cp .env.production.example .env  # then fill in real values
./scripts/deploy.sh               # first run, manually
```

Once that works, future pushes to `production` deploy automatically.

### 4. Promote `main` → `production`

Day-to-day, push to `main`. CI runs and gives you a green check. When you're ready to ship:

```bash
git checkout production
git merge --ff-only main
git push origin production
```

That's the only event that triggers `deploy.yml`. A failing CI on `production` blocks the SSH step entirely.

## Secrets that *don't* live in GitHub

`DATABASE_URL`, `POSTGRES_PASSWORD`, `SPOND_USERNAME`, `SPOND_PASSWORD`, `BUNNY_STORAGE_API_KEY`, AI provider keys, and the bcrypt-hashed admin password all live in `/opt/spondadmin/.env` on the server. They are intentionally **not** in GitHub Actions so a compromised workflow token can't exfiltrate them.

## Rotating the SSH host key

If the server is rebuilt or its host key changes, the deploy job will start failing with `Host key verification failed`. Regenerate the secret:

```bash
ssh-keyscan -H admin.lillehammerbueskyttere.no
```

Paste the output as the new `SSH_KNOWN_HOSTS` secret value.
