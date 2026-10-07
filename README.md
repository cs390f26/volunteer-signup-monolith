# Volunteer Signup

This repository contains the monolithic implementation of the Volunteer Signup application.

The Flask web application and DynamoDB run together on a single machine. The product specifications are maintained in the separate [Volunteer Signup specifications repository](https://github.com/ranayum/volunteer-signup-cloud-project).

## Documentation

- [Development setup](docs/development.md)
- [Deployment](docs/deploy.md)
- [Team Git process](docs/process.md)

## Quick start

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies and project package:

```bash
pip install -r requirements.txt
pip install -e .
```

Run the tests:

```bash
pytest
```

Start the application:

```bash
python -m volunteer_signup.app
```

Open [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health) to verify that the application is running.