"""Broker login functions — creates NorenApi instances for Shoonya and Flattrade."""

import warnings
from NorenRestApiPy.NorenApi import NorenApi
from .db import read_credentials

warnings.filterwarnings("ignore")


def login_shoonya(cred, db_path=None):
    """Authenticate to Shoonya using stored credentials (userid, pwd, sessionkey)."""
    class ShoonyaApiPy(NorenApi):
        def __init__(self):
            super().__init__(
                host='https://trade.shoonya.com/NorenWClientWeb/',
                websocket='wss://trade.shoonya.com/NorenWSWeb/'
            )
    api = ShoonyaApiPy()
    ret = api.set_session(
        userid=cred['username'][0],
        password=cred['pwd'][0],
        usertoken=cred['sessionkey'][0]
    )
    if not ret:
        raise Exception(f"Shoonya {cred['username'][0]} login failed")
    return api


def login_flattrade(cred, db_path=None):
    """Authenticate to Flattrade using stored credentials (userid, pwd, sessionkey)."""
    class FlatTradeApiPy(NorenApi):
        def __init__(self):
            super().__init__(
                host='https://piconnect.flattrade.in/PiConnectAPI/',
                websocket='wss://piconnect.flattrade.in/PiConnectWSTp/'
            )
    api = FlatTradeApiPy()
    ret = api.set_session(
        userid=cred['username'][0],
        password=cred['pwd'][0],
        usertoken=cred['sessionkey'][0]
    )
    if not ret:
        raise Exception(f"Flattrade {cred['username'][0]} login failed")
    return api


def broker_login(brokername, username, db_path=None):
    """Read broker credentials from DuckDB and return an authenticated NorenApi instance."""
    cred = read_credentials(brokername.upper(), username, db_path=db_path)
    if cred is None or cred.empty:
        raise ValueError(f"No credentials found for {brokername}/{username}")
    if brokername.lower() == "shoonya":
        return login_shoonya(cred, db_path=db_path)
    elif brokername.lower() == "flattrade":
        return login_flattrade(cred, db_path=db_path)
    else:
        raise ValueError(f"Unsupported broker: {brokername}")
