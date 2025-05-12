LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # Important! Prevents FastAPI/Uvicorn from overriding
    "formatters": {
        "default": {
            "()": "logging.Formatter",
            "fmt": "#%(levelname)s [%(asctime)s] %(filename)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        # Apply to all loggers (including Uvicorn)
        "": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}