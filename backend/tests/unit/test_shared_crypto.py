"""Unit tests for shared/crypto.py (Fernet-based secret encryption at rest)."""

from django.test import override_settings

from shared.crypto import decrypt_secret, encrypt_secret


class TestEncryptDecryptRoundTrip:
    def test_round_trip_returns_original_value(self):
        token = encrypt_secret("super-secret-value")
        assert decrypt_secret(token) == "super-secret-value"

    def test_encrypted_value_is_not_plaintext(self):
        token = encrypt_secret("super-secret-value")
        assert "super-secret-value" not in token

    def test_empty_string_encrypts_to_empty_string(self):
        assert encrypt_secret("") == ""

    def test_empty_string_decrypts_to_empty_string(self):
        assert decrypt_secret("") == ""

    def test_garbage_token_decrypts_to_empty_string_not_exception(self):
        assert decrypt_secret("not-a-real-fernet-token") == ""

    def test_decrypt_fails_safely_after_secret_key_rotation(self):
        token = encrypt_secret("super-secret-value")
        with override_settings(SECRET_KEY="a-completely-different-secret-key"):
            assert decrypt_secret(token) == ""
