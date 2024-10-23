"""
This script is meant to deploy the VM in the cloud.
"""

import urllib.request

import pulumi_aws as aws
import pulumi_cloudflare as cloudflare

# https://github.com/cloudflare/wrangler-legacy/issues/209#issuecomment-541654484
CLOUDFLARE_ACCOUNT_ID = "57ac323804932b01e44e546ff34ba9a3"

availability_zone = "us-east-2a"  # Ohio
blueprint_id = "ubuntu_22_04"
bundle_id = "micro_3_0"  # $7/month, 1GB, 2 vCPUs, 40GB SSD

url = "factorio.nathanv.app"

# donwload public key
with urllib.request.urlopen(
    "https://raw.githubusercontent.com/NathanVaughn/public-keys/main/ssh.pub"
) as response:
    public_key = response.read().decode()

ssh_key_pair = aws.lightsail.KeyPair(
    "ssh_key_pair", name="ssh_public_key", public_key=public_key
)

factorio_disk = aws.lightsail.Disk(
    "factorio_disk",
    availability_zone=availability_zone,
    size_in_gb=8,  # minimum is 8gb
    name="factorio_disk",
)

factorio_vps = aws.lightsail.Instance(
    "factorio_vps",
    name="factorio_server",
    availability_zone=availability_zone,
    blueprint_id=blueprint_id,
    bundle_id=bundle_id,
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
    "nathanv.app-zone",
    zone="nathanv.app",
    plan="free",
    account_id=CLOUDFLARE_ACCOUNT_ID,
)
cloudflare.Record(
    "nathanv.app-record-factorio",
    name=url,
    type="A",
    content=factorio_vps.public_ip_address,
    proxied=False,
    zone_id=zone.id,
)
