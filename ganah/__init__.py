"""Core exports for ganah — multi-broker authentication library."""

from .api import setup_api, place_live_order, order_status
from .session import broker_login
from .db import read_credentials, update_session_key, get_all_credentials, init_db, update_credentials
from .registry import get_auth_handler, get_broker_names, register_broker


def refresh_session(broker_name, username, db_path=None):
    """Run the appropriate broker login flow to refresh the session key.
    
    Args:
        broker_name: 'SHOONYA' or 'FLATTRADE'
        username: Broker account username
        db_path: Path to auth.duckdb (default: ganah/auth/auth.duckdb)
    
    Returns:
        (success: bool, message: str)
    """
    handler = get_auth_handler(broker_name)
    return handler.refresh_session(username, db_path=db_path)


__all__ = [
    "setup_api", "place_live_order", "order_status",
    "broker_login",
    "read_credentials", "update_session_key", "get_all_credentials", "init_db", "update_credentials",
    "get_auth_handler", "get_broker_names", "register_broker",
    "refresh_session",
]
