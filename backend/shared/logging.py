import json
import logging


class JsonFormatter(logging.Formatter):
    """
    Emits each log record as a single-line JSON object.

    Using json.dumps instead of a format string prevents broken JSON when the
    message or exception text contains quotes, newlines, or non-ASCII characters.
    """

    def format(self, record: logging.LogRecord) -> str:
        data: dict = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            data["stack"] = self.formatStack(record.stack_info)
        return json.dumps(data, ensure_ascii=False)
