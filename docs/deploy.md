# Deployment

## Local

Requires Docker and the `.venv` from [development.md](development.md).

```bash
scripts/run_local.sh
```

This starts DynamoDB Local, creates the tables, and runs the app at [http://127.0.0.1:5000](http://127.0.0.1:5000). Ctrl+C stops both. Load sample data with `python scripts/seed.py`.

## EC2

Launch an Amazon Linux 2023 instance with ports 22 and 80 open, and paste `deploy/userdata.sh` into User data. After a few minutes, open `http://<public-ip>/`.

`userdata.sh` clones `main`, so merge changes first. It installs the app and DynamoDB Local, then:

1. Starts `dynamodb-local.service` (port 8000).
2. Creates the tables with `scripts/create_tables.py`.
3. Starts `volunteer-signup.service` (gunicorn on port 80).

Both services run as `ec2-user` and restart on reboot. Port 8000 is not exposed, and no real AWS keys are used. The tables start empty; to load sample data, run `.venv/bin/python scripts/seed.py` in `~/volunteer-signup-monolith`.

Troubleshooting:

```bash
sudo cat /var/log/cloud-init-output.log
systemctl status dynamodb-local volunteer-signup
journalctl -u volunteer-signup -e
```
