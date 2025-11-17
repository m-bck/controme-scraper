import logging

def configure_logging(logger_name: str) -> logging.Logger:
    """
    Configures a logger with a given name, sets up a StreamHandler with a specific logging format, and sets the log level to DEBUG.

    Args:
        logger_name (str): The name of the logger to be configured.

    Returns:
        logging.Logger: The configured logger object.
    """

    logger = logging.getLogger(logger_name)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(name)s] [%(levelname)s] : %(message)s")
        # logging.Formatter("%(asctime)s %(name)-12s [%(levelname)-8s] : %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    return logger
