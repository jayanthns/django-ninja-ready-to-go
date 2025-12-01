import os

import django
import dramatiq
from django.utils.module_loading import autodiscover_modules

# ------------------------------------------------------------------------------
# 🐒 Patch Gevent if configured
# ------------------------------------------------------------------------------
# We check env vars directly because Django settings aren't loaded yet.
if os.getenv("DRAMATIQ_POOL", "gevent") == "gevent":
    try:
        from gevent import monkey

        monkey.patch_all()
    except ImportError:
        pass

# ------------------------------------------------------------------------------
# ⚙️ Setup Django
# ------------------------------------------------------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
django.setup()

# ------------------------------------------------------------------------------
# 🕵️ Auto-discover tasks
# ------------------------------------------------------------------------------
# This will look for 'tasks.py' (or 'actors.py' if you prefer, but 'tasks' is common)
# in all installed apps.
autodiscover_modules("tasks")
autodiscover_modules("actors")

# ------------------------------------------------------------------------------
# 📡 Expose Broker for CLI
# ------------------------------------------------------------------------------
broker = dramatiq.get_broker()
