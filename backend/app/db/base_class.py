"""Base class module for SQLAlchemy models."""
from typing import Any
import datetime

from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    """Base class for all models."""
    
    id: Any
    __name__: str
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:  # pylint: disable=no-self-argument
        return cls.__name__.lower()
    
    created_at = datetime.datetime.utcnow
    updated_at = None 