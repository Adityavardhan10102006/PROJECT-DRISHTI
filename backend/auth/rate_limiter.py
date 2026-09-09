"""
backend/auth/rate_limiter.py — Project DRISHTI
===============================================
Simple in-memory rate limiter for brute-force login protection.

Architecture:
  - Tracks failed login attempts per identifier (IP or username)
  - After MAX_FAILURES attempts: LOCKOUT_SECONDS lockout
  - Automatically expires lockouts — no persistent storage needed
  - Thread-safe for FastAPI's async workers

Limits are generous for hackathon/demo use:
  - 5 failed attempts → 15 min lockout
"""

import time
import threading
from typing import Dict, Tuple

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
MAX_FAILURES = 5
LOCKOUT_SECONDS = 15 * 60  # 15 minutes
ATTEMPT_WINDOW_SECONDS = 10 * 60  # Reset attempt count after 10 min of no failures


# ─────────────────────────────────────────────
# IN-MEMORY STORE
# ─────────────────────────────────────────────

_lock = threading.Lock()

# key → (failure_count, first_failure_timestamp, lockout_until_timestamp)
_attempts: Dict[str, Tuple[int, float, float]] = {}


def _clean_expired() -> None:
    """Remove entries whose lockout and attempt window have both expired."""
    now = time.time()
    expired_keys = [
        k for k, (count, first_ts, locked_until) in _attempts.items()
        if now > max(locked_until, first_ts + ATTEMPT_WINDOW_SECONDS)
    ]
    for k in expired_keys:
        del _attempts[k]


def is_locked_out(identifier: str) -> bool:
    """
    Check if an identifier is currently locked out.

    Args:
        identifier: IP address or username string

    Returns:
        True if the identifier is in lockout period
    """
    with _lock:
        if identifier not in _attempts:
            return False
        _, _, locked_until = _attempts[identifier]
        if time.time() < locked_until:
            return True
        # Lockout expired — clean up
        del _attempts[identifier]
        return False


def record_failure(identifier: str) -> Tuple[bool, int, int]:
    """
    Record a failed login attempt.

    Args:
        identifier: IP address or username string

    Returns:
        Tuple of (is_now_locked_out, failure_count, seconds_until_unlock)
    """
    now = time.time()
    with _lock:
        _clean_expired()

        if identifier in _attempts:
            count, first_ts, locked_until = _attempts[identifier]
            # Already locked out
            if now < locked_until:
                return True, count, int(locked_until - now)
            # Attempt window expired — reset
            if now > first_ts + ATTEMPT_WINDOW_SECONDS:
                count, first_ts = 0, now
        else:
            count, first_ts = 0, now

        count += 1
        locked_until = 0.0
        now_locked = False

        if count >= MAX_FAILURES:
            locked_until = now + LOCKOUT_SECONDS
            now_locked = True

        _attempts[identifier] = (count, first_ts, locked_until)
        seconds_remaining = int(locked_until - now) if now_locked else 0
        return now_locked, count, seconds_remaining


def record_success(identifier: str) -> None:
    """
    Clear failed attempt record on successful login.

    Args:
        identifier: IP address or username string
    """
    with _lock:
        _attempts.pop(identifier, None)


def get_attempts_remaining(identifier: str) -> int:
    """
    Return the number of attempts remaining before lockout.

    Args:
        identifier: IP address or username string

    Returns:
        Number of remaining attempts (0 if locked out)
    """
    with _lock:
        if identifier not in _attempts:
            return MAX_FAILURES
        count, first_ts, locked_until = _attempts[identifier]
        if time.time() < locked_until:
            return 0
        remaining = MAX_FAILURES - count
        return max(0, remaining)
