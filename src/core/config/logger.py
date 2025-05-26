LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,  # Prevents duplicate logs
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
        # Your app's logs (adjust "src" to your root package name)
        "src": {
            "handlers": ["console"],
            "level": "DEBUG",  # Debug for your code
            "propagate": False,
        },
        # Silence noisy libraries
        "uvicorn.error": {"level": "WARNING"},
        "uvicorn.access": {"level": "WARNING"},
        "watchfiles": {"level": "ERROR"},
        "passlib": {"level": "WARNING"},
        "bcrypt": {"level": "WARNING"},
    },
    # Root logger (catch-all)
    "root": {
        "handlers": ["console"],
        "level": "INFO",  # Only show INFO+ for unconfigured loggers
    },
}