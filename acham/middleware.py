from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from django.conf import settings
from django.utils import translation


@dataclass(frozen=True)
class _LanguageHeader:
    raw_value: str
    normalized: str
    code: Optional[str]


class LanguageFromHeaderMiddleware:
    """
    Activate the application language based on the custom ``Language`` HTTP header.

    The middleware converts the provided header into a valid Django language code,
    updates the request so downstream components (including ``LocaleMiddleware`` and
    django-modeltranslation) see the expected language, and restores the previous
    language after the response has been processed.
    """

    header_name = "Language"

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self._available_codes = {
            code.lower(): code for code, _ in settings.LANGUAGES
        }

    def __call__(self, request):
        previous_language = translation.get_language()
        language_header = self._parse_header(request)

        if language_header.code:
            self._activate_language(request, language_header.code)

        response = self.get_response(request)

        if language_header.code:
            self._restore_language(previous_language)

        return response

    def _parse_header(self, request) -> _LanguageHeader:
        value = request.headers.get(self.header_name) or request.META.get("HTTP_LANGUAGE")

        if not value:
            return _LanguageHeader(raw_value="", normalized="", code=None)

        normalized = value.strip().lower()
        candidate = normalized.split(",")[0].split(";")[0].replace("_", "-")

        # Attempt direct match (ru, en, uz)
        language_code = self._available_codes.get(candidate)

        # Fallback to primary part (e.g. en-us -> en)
        if not language_code and "-" in candidate:
            primary = candidate.split("-")[0]
            language_code = self._available_codes.get(primary)

        # Map some common aliases
        if not language_code:
            aliases = {
                "rus": "ru",
                "eng": "en",
                "uzb": "uz",
            }
            alias_target = aliases.get(candidate)
            if alias_target:
                language_code = self._available_codes.get(alias_target)

        return _LanguageHeader(raw_value=value, normalized=normalized, code=language_code)

    def _activate_language(self, request, language_code: str) -> None:
        request.META["HTTP_ACCEPT_LANGUAGE"] = language_code
        request.LANGUAGE_CODE = language_code
        translation.activate(language_code)

    def _restore_language(self, previous_language: Optional[str]) -> None:
        if previous_language:
            translation.activate(previous_language)
        else:
            translation.deactivate()

