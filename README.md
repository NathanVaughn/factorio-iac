# Factorio IAC

This repository contains the code to deploy and setup my Factorio server.

## How It Works

This repo generates files using the inputs in the `.env` file,
and uses [Pulumi](https://www.pulumi.com/) to run `secripts/deploy.py`
to deploy a server to AWS Lightsail. My Cloudflare account is also updated
with a DNS record to point at the server.

In that deployment, the `user_data` option is used to pass in a script
that downloads this repository and uses [pyinfra](https://pyinfra.com/) to run
`scripts/configure.py` to configure and start the server.

Backups are setup hourly to a [Backblaze](https://www.backblaze.com/cloud-storage)
B2 bucket.

## Usage

First off, don't use this for yourself. Many things like my Cloudflare account ID
and B2 bucket name are hardcoded.

Copy `.env.example` to `.env` and fill in the values. You'll need a user account
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
vtr update
```
