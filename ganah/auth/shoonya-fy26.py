#!/usr/bin/env python
# coding: utf-8
#
# ╔══════════════════════════════════════════════════════════════╗
# ║  PROTECTED FILE — Read-only on filesystem (attrib +R)       ║
# ║  Do NOT modify unless explicitly requested by filename.     ║
# ║  To edit: attrib -R "C:\ngen26\auth\shoonya-fy26.py"       ║
# ╚══════════════════════════════════════════════════════════════╝

import pyotp
import sys
import os
import datetime
import zoneinfo
import pandas as pd
import time

_IST = zoneinfo.ZoneInfo("Asia/Kolkata")
import warnings
import json
import duckdb
import requests
from urllib.parse import parse_qs

warnings.filterwarnings("ignore")

TG_BOT_TOKEN = "7886647655:AAGvIksjnxENsthP9Lb8FAv2D4AZjYCztB4"
TG_CHAT_ID = "1541230972"

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth.duckdb")
brokername = 'SHOONYA'
userid = 'FA138862'


def send_tg(msg):
    try:
        requests.get(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            params={"chat_id": TG_CHAT_ID, "text": msg},
            timeout=10
        )
    except Exception as e:
        print(f"TG alert failed: {e}")


def _db_conn(read_only=True):
    return duckdb.connect(DB_PATH, read_only=read_only)


def Read_StoredCreds_From_Database(brokername='SHOONYA', username='FA138862'):
    try:
        print(f"Reading credentials from DuckDB for {brokername} {username}")
        con = _db_conn(read_only=True)
        result = con.execute(
            "SELECT brokername, username, pwd, factor2, vc, apikey, secretkey, imei, sessionkey "
            "FROM authsession WHERE brokername = ? AND username = ?",
            (brokername, username)
        ).fetchone()
        con.close()
        if result:
            cols = ["brokername", "username", "pwd", "factor2", "vc", "apikey", "secretkey", "imei", "sessionkey"]
            return pd.DataFrame([list(result)], columns=cols)
        print("No credentials found")
        return None
    except Exception as e:
        print(f"Error reading credentials: {e}")
        return None


def Store_SessionKey_To_Database(brokername='SHOONYA', username='FA138862', sessionkey='notset'):
    try:
        con = _db_conn(read_only=False)
        con.execute(
            "UPDATE authsession SET sessionkey = ?, updateddatetime = ? "
            "WHERE brokername = ? AND username = ?",
            (sessionkey, datetime.datetime.now(_IST).isoformat(), brokername, username)
        )
        con.commit()
        con.close()
        print(f"Session key updated in DuckDB for {brokername} {username}")
    except Exception as e:
        print(f"Error updating session key: {e}")


cred = Read_StoredCreds_From_Database(brokername, userid)
if cred is not None and not cred.empty:
    print(cred)
    username_val = cred['username'][0]
    password_val = cred['pwd'][0]
    totp_secret = cred['factor2'][0]
else:
    print("Failed to read credentials")
    sys.exit(1)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

chrome_options = Options()
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-background-networking")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--remote-allow-origins=*")
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

driver = webdriver.Chrome(options=chrome_options)
found_jkey = None

try:
    print("\n" + "="*60)
    print("  SHOONYA LOGIN - TAB NAVIGATION METHOD")
    print("="*60)
    print(f"  User: {username_val}")

    totp = pyotp.TOTP(totp_secret).now()
    print(f"  TOTP: {totp}")

    driver.get("https://trade.shoonya.com/")

    # Wait for Flutter CanvasKit to fully load
    print("\n  Waiting for Flutter app to load...")
    time.sleep(8)

    # Click on the body to focus the Flutter canvas
    body = driver.find_element(By.TAG_NAME, "body")
    body.click()
    time.sleep(2)

    # Send Tab first to ensure focus is on the first input field
    print("\n  Tabbing to User ID field...")
    body.send_keys(Keys.TAB)
    time.sleep(1)

    print("  Entering User ID...")
    body.send_keys(username_val)
    time.sleep(1)

    print("  Tabbing to Password field...")
    body.send_keys(Keys.TAB)
    time.sleep(1)

    print("  Entering Password...")
    body.send_keys(password_val)
    time.sleep(1)

    print("  Tabbing to TOTP field...")
    body.send_keys(Keys.TAB)
    time.sleep(1)

    print("  Entering TOTP...")
    body.send_keys(totp)
    time.sleep(1)

    print("  Pressing Enter to login...")
    body.send_keys(Keys.ENTER)

    print("\n  Login submitted! Waiting for jKey in network traffic...")
    time.sleep(5)

    # Poll for jKey in network logs
    max_wait = 60
    poll_interval = 2
    waited = 0

    while waited < max_wait:
        time.sleep(poll_interval)
        waited += poll_interval

        logs = driver.get_log("performance")
        for entry in logs:
            try:
                message = json.loads(entry["message"])["message"]
                if message["method"] == "Network.requestWillBeSent":
                    request = message["params"]["request"]
                    post_data = request.get("postData", "")
                    if not post_data:
                        continue
                    params = parse_qs(post_data)
                    jkey = params.get("jKey", [None])[0]
                    if jkey and jkey.strip():
                        found_jkey = jkey
                        break
            except Exception:
                pass

        if found_jkey:
            print(f"  --> jKey detected after ~{waited} seconds!")
            break

        print(f"  Waiting for network traffic... ({waited}s)")

    if not found_jkey:
        print("\n  jKey not found via polling. Final scan of all logs...")
        logs = driver.get_log("performance")
        for entry in logs:
            try:
                message = json.loads(entry["message"])["message"]
                if message["method"] == "Network.requestWillBeSent":
                    request = message["params"]["request"]
                    post_data = request.get("postData", "")
                    if not post_data:
                        continue
                    params = parse_qs(post_data)
                    jkey = params.get("jKey", [None])[0]
                    if jkey and jkey.strip():
                        found_jkey = jkey
                        print(f"  --> jKey found in final scan!")
                        break
            except Exception:
                pass

    if found_jkey:
        print(f"\n  jKey: {found_jkey[:50]}...")
        Store_SessionKey_To_Database(
            brokername=brokername,
            username=userid,
            sessionkey=found_jkey
        )
        msg = f"Shoonya jKey captured and stored for {userid}"
        print(msg)
        send_tg(f"Shoonya jKey stored for {userid}")

        # Test login with captured jKey
        from NorenRestApiPy.NorenApi import NorenApi
        userToken = found_jkey
        try:
            class ShoonyaApiPy(NorenApi):
                def __init__(self):
                    NorenApi.__init__(self, host='https://trade.shoonya.com/NorenWClientWeb/', websocket='wss://trade.shoonya.com/NorenWSWeb/')
            api = ShoonyaApiPy()
        except Exception as e:
            class ShoonyaApiPy(NorenApi):
                def __init__(self):
                    NorenApi.__init__(self, host='https://trade.shoonya.com/NorenWClientWeb/', websocket='wss://trade.shoonya.com/NorenWSWeb/')
            api = ShoonyaApiPy()
        ret1 = api.set_session(username_val, password_val, userToken)
        print(f"  set_session result: {ret1}")
        account_details = pd.DataFrame([api.get_limits()])
        print(f"\n  Account Details:\n{account_details}")

        if ret1:
            try:
                order = api.place_order(
                    buy_or_sell='B',
                    product_type='I',
                    exchange='NSE',
                    tradingsymbol='RELIANCE-EQ',
                    quantity=2,
                    price_type='MKT',
                    price=0,
                    trigger_price=0,
                    retention='DAY',
                    amo='NO'
                )
            except Exception as e:
                print(f"  Test order skipped: {e}")
            print(f"\n  Test order response:\n{order}")
    else:
        print("\n  jKey not found. The login might have failed.")
        print("  Check the browser window to see what happened.")

finally:
    print("\n  Browser will close in 5 seconds...")
    time.sleep(5)
    driver.quit()

sys.exit("Exiting shoonya-fy26")
