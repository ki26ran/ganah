"""Broker registry — maps broker names to AuthHandler implementations."""

from .base import AuthHandler

_HANDLERS = {}


def register_broker(name, handler_cls):
    """Register a broker auth handler class by name."""
    if not issubclass(handler_cls, AuthHandler):
        raise TypeError(f"{handler_cls.__name__} must extend AuthHandler")
    _HANDLERS[name.upper()] = handler_cls


def get_auth_handler(name):
    """Get an AuthHandler instance for the given broker name.
    
    Built-in brokers are lazy-loaded on first access.
    """
    name = name.upper()
    if name not in _HANDLERS:
        if name == "SHOONYA":
            from .auth.shoonya import ShoonyaAuthHandler
            register_broker(name, ShoonyaAuthHandler)
        elif name == "FLATTRADE":
            from .auth.flattrade import FlatTradeAuthHandler
            register_broker(name, FlatTradeAuthHandler)
        else:
            raise ValueError(
                f"Unknown broker: {name}. Available: {', '.join(get_broker_names())}"
            )
    return _HANDLERS[name]()


def get_broker_names():
    """Return list of registered broker names."""
    return list(_HANDLERS.keys())
