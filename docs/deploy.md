# Deployment

The application and DynamoDB Local run together on one Amazon Linux 2023 EC2 instance. The files are in `deploy/`:

| File | Purpose |
|------|---------|
| `userdata.sh` | Installs packages, clones the repo, installs DynamoDB Local, installs the services, and creates the tables |
| `dynamodb-local.service` | systemd unit that runs DynamoDB Local as `ec2-user` on port 8000 |
| `volunteer-signup.service` | systemd unit that runs gunicorn as `ec2-user` on port 80, after DynamoDB Local answers |

`userdata.sh` clones the `main` branch, so merge changes before launching.

## Launch

In the EC2 console, launch an Amazon Linux 2023 instance with a security group that allows ports 22 and 80, and paste `deploy/userdata.sh` into the User data field.

Setup takes a few minutes. Then open `http://<public-ip>/` and `http://<public-ip>/health`.

## Startup order

1. `userdata.sh` starts `dynamodb-local.service`.
2. `scripts/wait_for_dynamodb.py` waits until DynamoDB Local answers.
3. `scripts/create_tables.py` creates any missing tables. It is safe to rerun.
4. `volunteer-signup.service` starts gunicorn, waiting for DynamoDB Local again first.

Both services are enabled, so they start in the same order after a reboot. The tables start empty; to load the sample events for a demo, run `.venv/bin/python scripts/seed.py` from the app directory.

## Troubleshooting

```bash
sudo cat /var/log/cloud-init-output.log
systemctl status dynamodb-local volunteer-signup
journalctl -u volunteer-signup -e
```

## Security

- Only ports 22 and 80 are open. DynamoDB Local listens on port 8000, which the security group does not expose.
- Both services run as `ec2-user`, not root. gunicorn gets only the capability to bind port 80.
- `.env` holds the dummy credentials from `config/example.env`, which DynamoDB Local accepts; no real AWS keys are on the instance.
