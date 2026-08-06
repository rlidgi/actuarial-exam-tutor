import logging
import sys


def configure_logging(app) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )

    level = logging.DEBUG if app.debug else logging.INFO
    app.logger.setLevel(level)
    app.logger.handlers = [handler]
