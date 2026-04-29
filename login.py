# login.py - Backend for simple login system
# Fixes applied per CodeSherlock analysis:
# - Modularity: UserStore + AuthService classes (no global state)
# - Dependency Injection: store and time_provider are injected
# - Exception Handling: try/except with logging on all public methods
# - Input Validation: username allow-list, length limits, html escaping
# - Resource Utilization: bounded OrderedDict store with max capacity
# - Monitoring & Logging: structured logging for all key auth events

import re
import html
import logging
from datetime import datetime
from collections import OrderedDict
from typing import Optional, Tuple, Dict

logger = logging.getLogger(__name__)

MAX_FAILED_ATTEMPTS_DEFAULT = 3
MAX_USERS_DEFAULT = 10_000
MAX_USERNAME_LEN = 64
MAX_PASSWORD_LEN = 256

# Allow-list: letters, digits, dot, underscore, hyphen; 3–64 chars
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{3,64}$")


def _is_valid_username(username: str) -> bool:
    if not isinstance(username, str):
        return False
    if not username.isprintable():
        return False
    return bool(USERNAME_RE.match(username))


class TimeProvider:
    """Abstraction for current time — replaceable in tests."""
    def now_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class UserStore:
    """
    Bounded in-memory user store backed by an OrderedDict.
    Evicts the oldest user when capacity is reached.
    """
    def __init__(self, max_users: int = MAX_USERS_DEFAULT):
        self._users: OrderedDict = OrderedDict()
        self.max_users = max_users

    def get_user(self, username: str) -> Optional[Dict]:
        return self._users.get(username)

    def save_user(self, username: str, user_dict: Dict) -> None:
        self._users[username] = user_dict
        self._users.move_to_end(username, last=True)

    def add_user(self, username: str, user_dict: Dict) -> None:
        # Evict oldest if at capacity
        while len(self._users) >= self.max_users:
            evicted, _ = self._users.popitem(last=False)
            logger.warning("UserStore: evicted oldest user due to capacity", extra={"evicted": evicted})
        self._users[username] = user_dict

    def has_user(self, username: str) -> bool:
        return username in self._users

    def list_usernames(self):
        return list(self._users.keys())


class AuthService:
    """
    Authentication logic decoupled from storage.
    Accepts injected UserStore and TimeProvider for testability.
    """
    def __init__(
        self,
        store: Optional[UserStore] = None,
        time_provider: Optional[TimeProvider] = None,
        max_failed_attempts: int = MAX_FAILED_ATTEMPTS_DEFAULT,
    ):
        self.store = store or UserStore()
        self.time_provider = time_provider or TimeProvider()
        self.max_failed_attempts = max_failed_attempts

    def register(self, username: str, password: str) -> Tuple[bool, str]:
        try:
            if not username or not password:
                logger.warning("register: empty username or password")
                return False, "Username and password cannot be empty."

            if len(username) > MAX_USERNAME_LEN:
                return False, f"Username too long (max {MAX_USERNAME_LEN} chars)."
            if len(password) > MAX_PASSWORD_LEN:
                return False, f"Password too long (max {MAX_PASSWORD_LEN} chars)."

            if not _is_valid_username(username):
                return False, "Invalid username: use letters, digits, '.', '_', '-' (3–64 chars)."

            if self.store.has_user(username):
                logger.info("register: duplicate user attempt", extra={"username": username})
                return False, f"User '{html.escape(username)}' already exists."

            self.store.add_user(username, {
                "password": password,
                "failed_attempts": 0,
                "locked": False,
                "created_at": self.time_provider.now_str(),
            })
            logger.info("register: user created", extra={"username": username})
            return True, f"User '{html.escape(username)}' registered successfully."

        except (TypeError, ValueError) as e:
            return False, str(e)
        except Exception:
            logger.exception("register: unexpected error for username=%r", username)
            return False, "An internal error occurred during registration."

    def authenticate(self, username: str, password: str) -> Tuple[bool, str]:
        try:
            if not _is_valid_username(username):
                return False, "Invalid username."

            user = self.store.get_user(username)
            if user is None:
                logger.warning("authenticate: user not found", extra={"username": username})
                return False, "User not found."

            locked = bool(user.get("locked", False))
            failed_attempts = int(user.get("failed_attempts", 0))
            stored_password = user.get("password")

            if locked:
                logger.warning("authenticate: locked account attempt", extra={"username": username})
                return False, f"Account '{html.escape(username)}' is locked due to too many failed attempts."

            if stored_password is None:
                logger.error("authenticate: corrupted user record (no password)", extra={"username": username})
                return False, "Account is not available."

            if stored_password != password:
                failed_attempts += 1
                user["failed_attempts"] = failed_attempts
                remaining = self.max_failed_attempts - failed_attempts

                if failed_attempts >= self.max_failed_attempts:
                    user["locked"] = True
                    self.store.save_user(username, user)
                    logger.error("authenticate: account locked", extra={"username": username, "failed_attempts": failed_attempts})
                    return False, f"Incorrect password. Account '{html.escape(username)}' is now locked."

                self.store.save_user(username, user)
                logger.warning("authenticate: wrong password", extra={"username": username, "failed_attempts": failed_attempts, "remaining": remaining})
                return False, f"Incorrect password. {remaining} attempt(s) remaining."

            # Successful login
            user["failed_attempts"] = 0
            self.store.save_user(username, user)
            logger.info("authenticate: login successful", extra={"username": username})
            return True, f"Welcome, {html.escape(username)}! Login successful."

        except (TypeError, ValueError) as e:
            return False, str(e)
        except Exception:
            logger.exception("authenticate: unexpected error for username=%r", username)
            return False, "An internal error occurred during authentication."

    def get_user_info(self, username: str) -> Optional[Dict]:
        try:
            user = self.store.get_user(username)
            if user is None:
                return None
            return {
                "username": username,
                "failed_attempts": int(user.get("failed_attempts", 0)),
                "locked": bool(user.get("locked", False)),
                "created_at": user.get("created_at"),
            }
        except Exception:
            logger.exception("get_user_info: unexpected error for username=%r", username)
            return None

    def unlock_account(self, username: str) -> Tuple[bool, str]:
        try:
            user = self.store.get_user(username)
            if user is None:
                return False, "User not found."
            user["locked"] = False
            user["failed_attempts"] = 0
            self.store.save_user(username, user)
            logger.info("unlock_account: account unlocked", extra={"username": username})
            return True, f"Account '{html.escape(username)}' has been unlocked."
        except Exception:
            logger.exception("unlock_account: unexpected error for username=%r", username)
            return False, "An internal error occurred while unlocking account."

    def list_users(self):
        try:
            return self.store.list_usernames()
        except Exception:
            logger.exception("list_users: unexpected error")
            return []
