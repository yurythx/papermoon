import datetime
import decimal
from typing import Any
import uuid

from rest_framework.renderers import JSONRenderer
from rest_framework.utils.encoders import JSONEncoder


class _ExtendedEncoder(JSONEncoder):
    """Extends DRF's encoder to handle UUID, Decimal, and date types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        if isinstance(obj, datetime.datetime | datetime.date):
            return obj.isoformat()
        return super().default(obj)


class UnifiedResponseRenderer(JSONRenderer):
    encoder_class = _ExtendedEncoder

    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: dict | None = None,
    ) -> bytes:
        response = renderer_context.get("response") if renderer_context else None
        status_code = response.status_code if response else 200
        success = status_code < 400

        if success:
            envelope = {"success": True, "data": data, "error": None}
        else:
            envelope = {"success": False, "data": None, "error": data}

        return self.encoder_class().encode(envelope).encode("utf-8")
