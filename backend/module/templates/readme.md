# Honeypot agent deployment templates

These files are served/rendered by the backend to deploy a honeypot agent on a
target server. Placeholders (`{{AGENT_ID}}`, `{{AGENT_TOKEN}}`, `{{SERVER_URL}}`,
…) are filled in per-agent by `route/agent/api_agent.py`.

## One-command deployment

On the target server (as root), a single command downloads, configures, starts
and enables-at-boot the agent — nothing to launch by hand:

```bash
curl -ksSL https://YOUR-SERVER/api/agent/install/<AGENT_ID> | sudo bash
```

The installer auto-selects the method: **Docker** if the Docker daemon is
already present (isolated container, `--restart unless-stopped`), otherwise a
**native systemd service** (`Restart=always`, enabled at boot). Force a method:

```bash
curl -ksSL https://YOUR-SERVER/api/agent/install/<AGENT_ID> | sudo bash -s -- --method docker
curl -ksSL https://YOUR-SERVER/api/agent/install/<AGENT_ID> | sudo bash -s -- --method direct
curl -ksSL https://YOUR-SERVER/api/agent/install/<AGENT_ID> | sudo bash -s -- --uninstall
```

## Files

- `install_agent.sh` — the installer (auto / docker / direct / manual / uninstall).
- `Dockerfile` — lightweight agent image (`python:3.11-alpine` + prebuilt wheels,
  no build toolchain). Used both as a reference and written by the installer's
  Docker method.
- `ssh_honeypot_agent.py` / `ftp_honeypot_agent.py` / `smb_honeypot_agent.py` —
  the agent script templates (`download_agent` renders the config into them).
