"""
This script is meant to deploy the VM in the cloud.
"""

import os
import urllib.request

import pulumi_aws as aws
import pulumi_cloudflare as cloudflare

from scripts import prepare
from scripts.common import CLOUDFLARE_ACCOUNT_ID, GENERATED_FILES_DIR

prepare.main()

availability_zone = "us-east-2a"  # Ohio

# donwload public key
with urllib.request.urlopen(
    "https://raw.githubusercontent.com/NathanVaughn/public-keys/main/ssh.pub"
) as response:
    public_key = response.read().decode()

ssh_key_pair = aws.lightsail.KeyPair(
    "ssh_key_pair", name="ssh_public_key", public_key=public_key
)

factorio_disk = aws.lightsail.Disk(
    "factorio_lightsail_disk",
    availability_zone=availability_zone,
    size_in_gb=5,
    name="factorio_disk",
)

# read kickstart file
with open(os.path.join(GENERATED_FILES_DIR, "kickstart.sh"), "r") as fp:
    kickstart = fp.read()


factorio_vps = aws.lightsail.Instance(
    "factorio_lightsail_vps",
    name="factorio_server",
    availability_zone=availability_zone,
    blueprint_id="ubuntu_22_04",
    bundle_id="micro_3_0",  # $7/month, 1GB, 2 vCPUs, 40GB SSD
    key_pair_name=ssh_key_pair.name,
    user_data=kickstart,
)

factorio_disk_attachment = aws.lightsail.Disk_attachment(
    "factorio_disk_attachment",
    disk_name=factorio_disk.name,
    instance_name=factorio_vps.name,
    disk_path="/factorio/",
)

# add cloudflare record
zone = cloudflare.Zone(
    "nathanv.app-zone",
    zone="nathanv.app",
    plan="free",
    account_id=CLOUDFLARE_ACCOUNT_ID,
)
cloudflare.Record(
    "nathanv.app-record-factorio",
    name="factorio.nathanv.app",
    type="A",
    value=factorio_vps.public_ip_address,
    proxied=True,
    zone_id=zone.id,
)
