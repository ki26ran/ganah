"""Flattrade session refresh — checks session validity and prints auth URL if expired."""

import os
import sys
import zoneinfo
from datetime import datetime

from ..base import AuthHandler
from ..db import read_credentials

_IST = zoneinfo.ZoneInfo("Asia/Kolkata")
API_KEY = "1e5e979458524cf2810943c542f91a5e"

_LOGIN_URL = f"https://auth.flattrade.in/?app_key={API_KEY}"


class FlatTradeAuthHandler(AuthHandler):
    """Handles Flattrade session key management.
    
    Flattrade uses OAuth — auto-refresh is not possible.
    This handler checks validity and provides the auth URL for manual login.
    """

    def refresh_session(self, username="FZ09213", db_path=None):
        """Check if the current Flattrade session is valid.
        
        If expired, returns the auth URL for manual login.
        The callback URL auto-exchanges the code and stores the token.
        
        Args:
            username: Flattrade user ID (default FZ09213)
            db_path: Path to auth.duckdb
        
        Returns:
            (success: bool, message: str)
        """
        cred = read_credentials("FLATTRADE", username, db_path=db_path)
        if cred is None or cred.empty:
            return False, f"No credentials found for FLATTRADE/{username}"

        sessionkey = cred['sessionkey'].iloc[0] if 'sessionkey' in cred.columns else None
        if not sessionkey:
            return False, f"No session key for {username}. Login at: {_LOGIN_URL}"

        password = cred['pwd'].iloc[0] if 'pwd' in cred.columns else ''
        
        try:
            from NorenRestApiPy.NorenApi import NorenApi

            class FlatTradeApi(NorenApi):
                def __init__(self):
                    super().__init__(
                        host="https://piconnect.flattrade.in/PiConnectAPI/",
                        websocket="wss://piconnect.flattrade.in/PiConnectWSTp/"
                    )

            api = FlatTradeApi()
            ret = api.set_session(userid=username, password=password, usertoken=sessionkey)
            if not ret:
                return False, f"Session invalid for {username}. Login at: {_LOGIN_URL}"

            limits = api.get_limits()
            if isinstance(limits, dict) and limits.get("stat") == "Ok":
                cash = limits.get('cash', '?')
                return True, f"Session valid for {username} — cash: {cash}"
            else:
                return False, f"Session expired for {username}. Login at: {_LOGIN_URL}"

        except Exception as e:
            return False, f"Session check error for {username}: {e}. Login at: {_LOGIN_URL}"


# Convenience function
def refresh_session(username="FZ09213", db_path=None):
    handler = FlatTradeAuthHandler()
    return handler.refresh_session(username, db_path=db_path)


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "FZ09213"
    db_path = sys.argv[2] if len(sys.argv) > 2 else None
    success, msg = refresh_session(username, db_path=db_path)
    print(f"{'OK' if success else 'FAIL'}: {msg}")
    sys.exit(0 if success else 1)
