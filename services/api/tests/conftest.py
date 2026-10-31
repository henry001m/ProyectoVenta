import os

# The application creates its schema on import in development. Keep test collection
# isolated from a developer's configured PostgreSQL instance.
os.environ["DATABASE_URL"] = "sqlite://"
