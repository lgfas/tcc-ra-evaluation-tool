from django.apps import apps
from django.test.runner import DiscoverRunner


class ProjectTestRunner(DiscoverRunner):
    """Discover local domain apps regardless of the shell's working directory."""

    def build_suite(self, test_labels=None, **kwargs):
        labels = test_labels or [app.name for app in apps.get_app_configs() if app.name.startswith('apps.')]
        return super().build_suite(labels, **kwargs)
