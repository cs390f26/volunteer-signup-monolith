# Git and GitHub Process

This document explains how the team collaborates with Git and GitHub.

## Main branch

The `main` branch contains reviewed and working code. Team members should not develop features directly on `main` after the initial project setup.

## Starting new work

Before creating a branch, update the local `main` branch:

```bash
git switch main
git pull origin main
```

Create a new branch with a short descriptive name:

```bash
git switch -c feature-name
```

## Committing work

Check the changed files:

```bash
git status
```

Add only the files related to the current task and create a clear commit:

```bash
git add path/to/file
git commit -m "Describe the completed change"
```

Push the branch to GitHub:

```bash
git push -u origin feature-name
```

## Pull requests

All feature changes must be merged through a pull request.

Before merging:

- Confirm that the automated tests pass.
- Confirm that Ruff passes.
- Review the changed files.
- Check that the change matches the specifications.
- Resolve any merge conflicts.

After a pull request is merged, each team member should update their local `main` branch before starting new work.

## Team responsibilities

- Rana owns the API routes, validation, integration tests, and CI.
- Jack owns the DynamoDB layer, table setup, and sample-data tools.
- Riley owns the Flask templates, static files, and UI behavior.
- Deployment and final integration are shared responsibilities.