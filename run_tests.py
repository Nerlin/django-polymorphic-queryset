import sys
from django.conf import settings
from django.core.management import execute_from_command_line


if not settings.configured:
    settings.configure(
        DEBUG=False,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "polymorphic_queryset_tests"
            }
        },
        TEST_RUNNER="django.test.runner.DiscoverRunner",
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.messages',
            'django.contrib.sites',
            'django.contrib.admin',
            'polymorphic_queryset.tests',
        ),
        MIDDLEWARE_CLASSES=(),
        ROOT_URLCONF=[],
    )


def runtests():
    script, *args = sys.argv
    if args:
        command, *args = args
    else:
        command, *args = "test", "--traceback" 

    argv = sys.argv[:1] + [command, *args]
    execute_from_command_line(argv)


if __name__ == '__main__':
    runtests()
