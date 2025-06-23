"""Auxiliary functions for localization."""

import gettext
import os
from functools import wraps
from typing import Callable, Any


LOCALES = ['en_US.utf8', 'ru_RU.utf8']
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOCALE_DIR = os.path.join(BASE_DIR, "locales")

# Простейшее хранилище языков для каждого пользователя
user_langs = {}


def set_locale(lang: str):
    """Set locale."""
    if lang not in LOCALES:
        lang = "ru_RU.utf8"
    try:
        translation = gettext.translation("TG_bot", LOCALE_DIR, languages=[lang], fallback=True)
        translation.install()
    except Exception as e:
        print(f"Error loading translation for {lang}: {e}")


def get_user_lang(user_id: int) -> str:
    """Get use language by id."""
    return user_langs.get(user_id, "ru_RU.utf8")


def with_locale(handler: Callable) -> Callable:
    """Set language for function."""
    @wraps(handler)
    async def wrapper(event: Any, *args, **kwargs):
        user_id = getattr(event.from_user, "id", None)
        lang = get_user_lang(user_id) if user_id else "ru_RU.utf8"
        set_locale(lang)
        return await handler(event, *args, **kwargs)
    return wrapper
