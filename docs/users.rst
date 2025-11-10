 .. _users:

Users
======================================================================

Starting a new project, it’s highly recommended to set up a custom user model, 
even if the default User model is sufficient for you. 

This model behaves identically to the default user model, 
but you’ll be able to customize it in the future if the need arises.

.. automodule:: acham.users.models
   :members:
   :noindex:


API Authentication
------------------

The REST API now exposes unified authentication flows that cover email/password,
phone-based OTP and social providers (Google, Facebook).  All endpoints are
available under the ``/api/auth/`` prefix.

Required environment variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set the following variables in ``.env`` or the deployment environment:

* ``ESKIZ_EMAIL`` / ``ESKIZ_PASSWORD`` / ``ESKIZ_SENDER`` (and optional ``ESKIZ_CALLBACK_URL``)
* ``GOOGLE_OAUTH_CLIENT_ID`` / ``GOOGLE_OAUTH_CLIENT_SECRET`` / ``GOOGLE_OAUTH_SCOPES`` (space separated)
* ``FACEBOOK_OAUTH_CLIENT_ID`` / ``FACEBOOK_OAUTH_CLIENT_SECRET`` / ``FACEBOOK_OAUTH_SCOPES`` (comma separated)

REST endpoints
~~~~~~~~~~~~~~

* ``POST /api/auth/register/email`` – create an account with email/password
* ``POST /api/auth/register/phone/request`` – send Eskiz OTP for phone sign-up
* ``POST /api/auth/register/phone/confirm`` – verify OTP and finish phone sign-up
* ``POST /api/auth/login`` – obtain JWT tokens using email **or** phone + password
* ``POST /api/auth/login/refresh`` / ``POST /api/auth/login/verify`` – Simple JWT helpers
* ``POST /api/auth/login/phone/request`` – request OTP for phone login
* ``POST /api/auth/login/phone/verify`` – verify OTP and receive JWT tokens
* ``GET /api/auth/social/<provider>/authorize`` – retrieve OAuth redirect URL
* ``POST /api/auth/social/<provider>/callback`` – exchange ``code`` + ``state`` for JWT tokens

On successful registration or login the API responds with both ``access`` and
``refresh`` JWT tokens along with the serialized user payload.

