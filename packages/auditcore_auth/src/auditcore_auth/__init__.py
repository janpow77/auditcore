"""auditcore_auth – password hashing and JWT for the auditcore applications.

Framework-free core; bcrypt, argon2-cffi, PyJWT and FastAPI are optional
extras imported only when used. No cryptography is implemented here.
"""

from __future__ import annotations

from .clock import Clock, fixed_clock, system_clock
from .compare import constant_time_equals
from .compat import APP_PROFILES, AppProfile, app_profile
from .errors import (
    AuthError,
    BackendUnavailableError,
    ConfigurationError,
    DisallowedAlgorithmError,
    ExpiredTokenError,
    ImmatureTokenError,
    InvalidClaimError,
    InvalidSignatureError,
    MalformedTokenError,
    MissingClaimError,
    PasswordPolicyError,
    TokenError,
    TokenTypeError,
)
from .password_profiles import (
    ARGON2ID,
    BCRYPT,
    BCRYPT_PASSLIB,
    PASSWORD_PROFILES,
    Argon2Parameters,
    HashInfo,
    HashScheme,
    PasswordProfile,
    identify_hash,
    password_profile,
)
from .passwords import PasswordCheck, PasswordHasher
from .token_profiles import DEFAULT_TOKEN_PROFILE, TokenProfile
from .tokens import IssuedToken, TokenIssuer, TokenVerifier, VerifiedToken

__version__ = "0.1.0"

__all__ = [
    "APP_PROFILES",
    "ARGON2ID",
    "BCRYPT",
    "BCRYPT_PASSLIB",
    "DEFAULT_TOKEN_PROFILE",
    "PASSWORD_PROFILES",
    "AppProfile",
    "Argon2Parameters",
    "AuthError",
    "BackendUnavailableError",
    "Clock",
    "ConfigurationError",
    "DisallowedAlgorithmError",
    "ExpiredTokenError",
    "HashInfo",
    "HashScheme",
    "ImmatureTokenError",
    "InvalidClaimError",
    "InvalidSignatureError",
    "IssuedToken",
    "MalformedTokenError",
    "MissingClaimError",
    "PasswordCheck",
    "PasswordHasher",
    "PasswordPolicyError",
    "PasswordProfile",
    "TokenError",
    "TokenIssuer",
    "TokenProfile",
    "TokenTypeError",
    "TokenVerifier",
    "VerifiedToken",
    "__version__",
    "app_profile",
    "constant_time_equals",
    "fixed_clock",
    "identify_hash",
    "password_profile",
    "system_clock",
]
