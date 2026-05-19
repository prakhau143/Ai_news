import sys
from django.apps import AppConfig


class AgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.agent'

    def ready(self):
        # Don't start agent during management commands like migrate/collectstatic
        skip_commands = {'migrate', 'makemigrations', 'collectstatic', 'shell',
                         'createsuperuser', 'test', 'check'}
        if any(cmd in sys.argv for cmd in skip_commands):
            return

        # Only start in the main process (avoid double start with reloader)
        import os
        if os.environ.get('RUN_MAIN') == 'true' or 'runserver' not in sys.argv:
            from apps.agent.tasks import start_agent
            start_agent()
