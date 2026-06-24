"""
Management command to generate an RSA-2048 key pair for JWT RS256 signing.

Usage:
    python manage.py generate_jwt_keys

Output: two lines ready to paste into your .env file:
    JWT_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nMIIE...
    JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----\nMIIB...
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate an RSA-2048 key pair for JWT RS256 and print .env-ready values."

    def handle(self, *args, **options) -> None:
        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
        except ImportError:
            self.stderr.write(
                self.style.ERROR(
                    "The 'cryptography' package is required. "
                    "Install it with: pip install cryptography"
                )
            )
            return

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )

        private_pem = (
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            .decode()
            .replace("\n", "\\n")
            .strip()
        )
        public_pem = (
            private_key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode()
            .replace("\n", "\\n")
            .strip()
        )

        self.stdout.write(self.style.SUCCESS("# Paste these into your .env file:\n"))
        self.stdout.write(f"JWT_PRIVATE_KEY={private_pem}")
        self.stdout.write(f"JWT_PUBLIC_KEY={public_pem}")
        self.stdout.write(
            self.style.WARNING(
                "\n# Keep JWT_PRIVATE_KEY secret — never commit it to version control."
            )
        )
