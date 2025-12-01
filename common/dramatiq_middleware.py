import django
from dramatiq.middleware import Middleware


class DjangoDBConnectionsMiddleware(Middleware):
    """
    Middleware to close Django database connections after each task is processed.
    This is crucial to prevent connection leaks and 'connection closed' errors
    when running Dramatiq workers.
    """

    def after_process_message(self, broker, message, *, result=None, exception=None):
        django.db.connections.close_all()
