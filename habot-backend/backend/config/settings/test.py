from .development import *  # noqa: F403

# Tests remain fully containerized but never create temporary databases in Neon.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
TEST_DATA_API_ENABLED = True
