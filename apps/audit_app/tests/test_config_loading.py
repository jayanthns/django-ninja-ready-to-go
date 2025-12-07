import importlib

from django.test import override_settings

from apps.audit_app.v1 import task_dispatcher


class TestTaskDispatcherConfig:

    @override_settings(AUDIT_USE_CELERY=False, AUDIT_USE_DRAMATIQ=True)
    def test_load_dramatiq_config(self):
        # Reload module to pick up new settings
        importlib.reload(task_dispatcher)

        # Check if right tasks are assigned
        # We can check if the assigned function matches the dramatiq one
        from apps.audit_app.v1.tasks import audit_log_create_dramatiq_task

        assert task_dispatcher.audit_log_create_task == audit_log_create_dramatiq_task

    @override_settings(AUDIT_USE_CELERY=True, AUDIT_USE_DRAMATIQ=False)
    def test_load_celery_config(self):
        importlib.reload(task_dispatcher)

        from apps.audit_app.v1.tasks import audit_log_create_celery_task

        assert task_dispatcher.audit_log_create_task == audit_log_create_celery_task

    @override_settings(AUDIT_USE_CELERY=False, AUDIT_USE_DRAMATIQ=False)
    def test_load_fallback_config(self):
        importlib.reload(task_dispatcher)

        assert task_dispatcher.audit_log_create_task is None
        assert task_dispatcher.audit_log_update_task is None
        assert task_dispatcher.audit_log_delete_task is None

    def teardown_method(self):
        # Restore default (Celery=True) to avoid side effects on other tests
        # Assuming default settings have AUDIT_USE_CELERY=True or it defaults to True in code (getattr(..., True))
        # We can just reload without override, but we are inside override_settings context in tests.
        # Wait, override_settings undoes changes after test.
        # BUT we reloaded the module with the overridden settings. The module object in sys.modules is now the "wrong" one for other tests.
        # So we MUST reload it again with original settings.

        # Since teardown runs after override_settings restores settings,
        # we can just reload here.
        importlib.reload(task_dispatcher)
