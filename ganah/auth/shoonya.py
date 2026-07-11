"""Shoonya session refresh — wraps shoonya-fy26.py via subprocess (no edits to original)."""

import os
import subprocess
import sys

from ..base import AuthHandler

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_FY26_PATH = os.path.join(_SCRIPT_DIR, "shoonya-fy26.py")


class ShoonyaAuthHandler(AuthHandler):
    """Handles Shoonya session key refresh via Selenium Chrome jKey capture."""

    def refresh_session(self, username="FA138862", db_path=None):
        """Run shoonya-fy26.py to capture a fresh jKey.
        
        Requires Chrome + chromedriver (Selenium Manager auto-downloads).
        On headless Linux, run with: DISPLAY=:99 xvfb-run python ...
        
        Args:
            username: Shoonya user ID (default FA138862)
            db_path: Not used directly — shoonya-fy26.py uses its own DB path.
                     For custom paths, symlink or copy auth.duckdb.
        
        Returns:
            (success: bool, message: str)
        """
        if not os.path.exists(_FY26_PATH):
            return False, f"shoonya-fy26.py not found at {_FY26_PATH}"

        env = os.environ.copy()
        if "DISPLAY" not in env and sys.platform == "linux":
            env["DISPLAY"] = ":99"

        try:
            result = subprocess.run(
                [sys.executable, _FY26_PATH],
                cwd=_SCRIPT_DIR,
                capture_output=True,
                text=True,
                timeout=180
            )
            if result.returncode == 0:
                # Find jKey line in output
                for line in result.stdout.splitlines():
                    if "jKey:" in line or "jKey captured" in line:
                        return True, line.strip()
                return True, "Session refreshed (check logs for details)"
            else:
                # Error output
                err = (result.stderr or result.stdout)[:500]
                return False, f"shoonya-fy26 failed: {err}"
        except subprocess.TimeoutExpired:
            return False, "Shoonya login timed out (180s)"
        except Exception as e:
            return False, f"Shoonya refresh error: {e}"


# Convenience function
def refresh_session(username="FA138862", db_path=None):
    handler = ShoonyaAuthHandler()
    return handler.refresh_session(username, db_path=db_path)


if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else "FA138862"
    success, msg = refresh_session(username)
    print(f"{'OK' if success else 'FAIL'}: {msg}")
    sys.exit(0 if success else 1)
