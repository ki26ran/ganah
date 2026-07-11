# Ganah

Multi-broker authentication and API library for Indian stock brokers.

Supports:
- **Shoonya** — Selenium-based jKey capture + NorenApi
- **Flattrade** — OAuth-based token refresh + NorenApi

## Usage

```python
from ganah import setup_api

api = setup_api("SHOONYA", "FA138862", db_path="ganah/auth/auth.duckdb")
limits = api.get_limits()
```

## Refresh Session

```python
from ganah import refresh_session

# Shoonya: launches Chrome to capture fresh jKey
success, msg = refresh_session("SHOONYA", "FA138862")

# Flattrade: checks validity, prints auth URL if expired
success, msg = refresh_session("FLATTRADE", "FZ09213")
```
