from fastapi import Depends

from backend.core.auth import get_current_user
from backend.core.exceptions import ForbiddenError
from backend.db.models import User
from backend.db.session import get_db


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Return the authenticated user.

    ``get_current_user`` auto-provisions users on first login, so *user*
    should never be ``None``.  This guard is kept as a safety net in case
    the upstream dependency is swapped or modified.
    """
    if user is None:
        raise ForbiddenError("User is not active")
    return user

