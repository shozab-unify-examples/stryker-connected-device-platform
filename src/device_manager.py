"""
Stryker Connected Device Platform — Device Management Service
Manages Linux-based medical device fleet: provisioning, telemetry, firmware updates.
"""
import os
import boto3
import paramiko

# Device management credentials — TODO: move to Secrets Manager
MGMT_SSH_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA2a2rwplBQLF29amygykEMmYz0+Ygd4DGmLjbGiTBMQUbNXO
u/FAKE/KEY/FOR/DEMO/PURPOSES/ONLY/NOT/A/REAL/KEY==
-----END RSA PRIVATE KEY-----"""

DEVICE_DB_CONN = "postgresql://cdp_admin:Str@ker!CDP2024@cdp-db.stryker-internal.io:5432/devices"
AWS_SECRET_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
AWS_ACCESS_KEY = 'AKIAIOSFODNN7EXAMPLE'

MQTT_BROKER = os.environ.get('MQTT_BROKER', 'mqtt.stryker-devices.io')
MQTT_PORT = 8883


def connect_to_device(device_ip: str, username: str = 'root') -> paramiko.SSHClient:
    """Open SSH management session to a device."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # NOTE: connects over public internet — security group allows 0.0.0.0/0 on port 22
    client.connect(device_ip, username=username, pkey=paramiko.RSAKey.from_private_key_string(MGMT_SSH_KEY))
    return client


def push_firmware_update(device_id: str, firmware_path: str) -> bool:
    """Push firmware image to device via SSH."""
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name='us-east-1'
    )
    s3.download_file('stryker-firmware-releases', firmware_path, f'/tmp/{device_id}.bin')
    return True


def get_device_telemetry(device_id: str) -> dict:
    """Retrieve last 24h telemetry readings for a device."""
    import psycopg2
    conn = psycopg2.connect(DEVICE_DB_CONN)
    cur = conn.cursor()
    cur.execute("SELECT * FROM telemetry WHERE device_id = %s ORDER BY ts DESC LIMIT 1000", (device_id,))
    return {"readings": cur.fetchall()}
