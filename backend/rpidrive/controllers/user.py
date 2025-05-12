from typing import Optional

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import QuerySet

from rpidrive.controllers.exceptions import (
    InvalidOperationRequestException,
    NoPermissionException,
    ObjectNotFoundException,
)


class UserNotFoundException(ObjectNotFoundException):
    """User not found exception"""


class InvalidUsernameException(Exception):
    """Invalid username exception"""


class InvalidPasswordException(Exception):
    """Invalid password exception"""


def create_user(
    user: User, username: str, email: str, password: str, superuser: bool, **kwargs
) -> User:
    """Create user"""
    if not user.is_superuser:
        raise NoPermissionException("No permission.")
    username = username.strip()
    if not username:
        raise InvalidUsernameException("Invalid username.")
    password = password.strip()
    if not password:
        raise InvalidPasswordException("Invalid password.")

    if superuser:
        return User.objects.create_superuser(username, email, password, **kwargs)

    return User.objects.create_user(username, email, password, **kwargs)


def get_users(_user: User) -> QuerySet:
    """Get users"""
    return User.objects


def get_user(user: User, user_pk: int) -> User:
    """Get user object"""
    if user.pk == user_pk:
        return user
    if not user.is_superuser:
        raise NoPermissionException("No permission.")
    r_user = User.objects.filter(pk=user_pk).first()
    if not r_user:
        raise UserNotFoundException("User not found.")
    return r_user


def update_user(
    user: User,
    user_pk: int,
    email: str,
    password: Optional[str],
    superuser: bool,
    **kwargs
) -> User:
    """Update user"""
    if not user.is_superuser and user.pk != user_pk:
        raise NoPermissionException("No permission.")

    with transaction.atomic():
        target_user = User.objects.filter(pk=user_pk).select_for_update().first()
        if not target_user:
            raise UserNotFoundException("User not found.")

        target_user.email = email
        if user == target_user:
            if user.is_superuser != superuser:
                raise InvalidOperationRequestException(
                    "Can't upgrade/downgrade yourself."
                )
            if "is_active" in kwargs and kwargs["is_active"] != target_user.is_active:
                raise InvalidOperationRequestException("Can't deactivate yourself.")

        target_user.is_superuser = superuser
        for key, value in kwargs.items():
            setattr(target_user, key, value)
        if password:
            target_user.set_password(password)
        target_user.save()


def delete_user(user: User, user_pk: int):
    """Delete user"""
    if not user.is_superuser:
        raise NoPermissionException("No permission.")
    if user.id == user_pk:
        raise InvalidOperationRequestException("Can't delete yourself.")

    count, _ = User.objects.filter(pk=user_pk).all().delete()
    if not count:
        raise UserNotFoundException("User not found.")
