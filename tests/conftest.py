def pytest_configure():
    from django.conf import settings

    settings.configure(
        DEBUG=True,
        SECRET_KEY="test",
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        ROOT_URLCONF="tests.urls",
        ALLOWED_HOSTS=["*"],
    )
