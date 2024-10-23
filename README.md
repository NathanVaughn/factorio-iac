# Factorio IAC

This repository contains the code to deploy and setup my Factorio server.

## How It Works

This repo generates files using the inputs in the `config.py` file,
and uses [Pulumi](https://www.pulumi.com/) to run `deploy/main.py`
to deploy a server to AWS Lightsail. My Cloudflare account is also updated
with a DNS record to point at the server.

After that deployment, [pyinfra](https://pyinfra.com/) is used to run
`configure/configure.py` to configure and start the server.

Backups are setup hourly to a [Backblaze](https://www.backblaze.com/cloud-storage)
B2 bucket.

## Usage

Copy `config.example`.py to `config.py` and fill in the values. You'll need a user account
setup in AWS IAM with more or less all permissions in Lightsail to create
all the needed resources.

Install everything with:

```bash
# Install uv
# https://docs.astral.sh/uv/getting-started/installation/
uv tool install vscode-task-runner
vtr install
```

And deploy with:

```bash
vtr deploy
```
