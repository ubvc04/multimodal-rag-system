"""SQLAlchemy declarative base and model imports."""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

from app.models.document import Document  # noqa: E402,F401
from app.models.query_log import QueryLog  # noqa: E402,F401
from app.models.user import User  # noqa: E402,F401
