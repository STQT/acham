"""Custom SMTP email backend that disables SSL certificate verification.

This is useful for internal SMTP servers with self-signed certificates.
For production use, it's recommended to use proper certificates.
"""
import ssl

from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend
from django.utils.functional import cached_property


class EmailBackend(DjangoSMTPBackend):
    """SMTP email backend with disabled SSL certificate verification."""

    @cached_property
    def ssl_context(self):
        """Create SSL context with disabled certificate verification."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context
