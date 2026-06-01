import logging


def configure_logging(logger_name: str) -> logging.Logger:
    """
    Returns a logger for the given name. Adds a NullHandler if no handlers are
    configured, so the library is silent by default (per logging best practices).

    Args:
        logger_name (str): The name of the logger to be configured.

    Returns:
        logging.Logger: The configured logger object.
    """
    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger
