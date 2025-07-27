from mywhiskies.extensions import db

# Import all models to ensure they're registered with SQLAlchemy
from mywhiskies.models import (  # noqa: F401
    Bottle,
    BottleImage,
    Bottler,
    BottleTypes,
    Distillery,
    User,
    bottle_distillery,
)


def init_db():
    """Initialize database with all models loaded."""
    db.create_all()


def drop_db():
    """Drop all database tables."""
    db.drop_all()


def reset_db():
    """Drop and recreate all database tables."""
    db.drop_all()
    db.create_all()


def get_or_create(session, model, defaults=None, **kwargs):
    """Get an existing instance or create a new one."""
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items())
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True
