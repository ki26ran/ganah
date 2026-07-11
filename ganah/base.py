"""Abstract interfaces for broker auth handlers."""

from abc import ABC, abstractmethod


class AuthHandler(ABC):
    """Abstract base for broker-specific authentication handlers."""

    @abstractmethod
    def refresh_session(self, username, db_path=None):
        """Refresh the session key for the given broker username.
        
        Args:
            username: Broker account username (e.g. 'FA138862')
            db_path: Optional path to auth.duckdb
        
        Returns:
            (success: bool, message: str)
        """
        pass
