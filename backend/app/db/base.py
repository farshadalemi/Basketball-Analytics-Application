"""Import all the models, so that Base has them before being imported by Alembic."""
# Import the Base class first
from app.db.base_class import Base  # noqa

# Now import the models that use it
# pylint: disable=wrong-import-position
from app.models.user import User  # noqa
from app.models.video import Video  # noqa 