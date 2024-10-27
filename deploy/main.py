"""
This script is meant to deploy the VM in the cloud.
"""

import sys
import urllib.request

import pulumi_aws as aws
import pulumi_cloudflare as cloudflare

sys.path.append("..")

from config import (
    AWS_AVAILABILITY_ZONE,
    AWS_LIGHTSAIL_BLUEPRINT_ID,
    AWS_LIGHTSAIL_BUNDLE_ID,
    CLOUDFLARE_ACCOUNT_ID,
    CLOUDFLARE_ZONE,
    FACTORIO_SERVER_HOSTNAME,
    SSH_PUBLIC_KEY_URL,
)

# donwload public key
with urllib.request.urlopen(SSH_PUBLIC_KEY_URL) as response:
    public_key = response.read().decode()

ssh_key_pair = aws.lightsail.KeyPair(
    "ssh_key_pair", name="ssh_public_key", public_key=public_key
)

factorio_disk = aws.lightsail.Disk(
    "factorio_disk",
    availability_zone=AWS_AVAILABILITY_ZONE,
    size_in_gb=8,  # minimum is 8gb
    name="factorio_disk",
)

factorio_vps = aws.lightsail.Instance(
    "factorio_vps",
    name="factorio_server",
    availability_zone=AWS_AVAILABILITY_ZONE,
    blueprint_id=AWS_LIGHTSAIL_BLUEPRINT_ID,
    bundle_id=AWS_LIGHTSAIL_BUNDLE_ID,
    key_pair_name=ssh_key_pair.name,
)

# https://docs.aws.amazon.com/lightsail/latest/userguide/create-and-attach-additional-block-storage-disks-linux-unix.html
factorio_disk_attachment = aws.lightsail.Disk_attachment(
    "factorio_disk_attachment",
    disk_name=factorio_disk.name,
    instance_name=factorio_vps.name,
    disk_path="/dev/xvdf",
)

factorio_vps_public_ports = aws.lightsail.InstancePublicPorts(
    "factorio_vps_public_ports",
    instance_name=factorio_vps.name,
    port_infos=[
        {
            "from_port": 34197,
            "to_port": 34197,
            "protocol": "udp",
            "cidrs": ["0.0.0.0/0"],
            "ipv6_cidrs": ["::/0"],
        },
        {
            "from_port": 27015,
            "to_port": 27015,
            "protocol": "tcp",
            "cidrs": ["0.0.0.0/0"],
            "ipv6_cidrs": ["::/0"],
        },
        {
            "from_port": 22,
            "to_port": 22,
            "protocol": "tcp",
            # allow all IPs to ssh into the server
            "cidrs": ["0.0.0.0/0"],
            "ipv6_cidrs": ["::/0"],
        },
    ],
)

# add cloudflare record
zone = cloudflare.Zone(
    "cf-zone",
    zone=CLOUDFLARE_ZONE,
    plan="free",
    account_id=CLOUDFLARE_ACCOUNT_ID,
)
cloudflare.Record(
    "cf-record-factorio-ipv4",
    name=FACTORIO_SERVER_HOSTNAME,
    type="A",
    content=factorio_vps.public_ip_address,
    proxied=False,
    zone_id=zone.id,
)
cloudflare.Record(
    "cf-record-factorio-ipv6",
    name=FACTORIO_SERVER_HOSTNAME,
    type="AAAA",
    content=factorio_vps.ipv6_addresses[0],
    proxied=False,
    zone_id=zone.id,
)
