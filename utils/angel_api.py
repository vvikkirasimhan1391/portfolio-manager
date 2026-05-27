"""
Angel One SmartAPI Integration
Fetches live holdings, positions and profile data from Angel One.

Requirements:
    pip install smartapi-python pyotp

How to get credentials:
    1. Log in to https://smartapi.angelbroking.com/
    2. Create an app to get your API key
    3. Your Client ID is your Angel One login ID
    4. Your Password is your Angel One trading PIN
    5. Enable TOTP in Angel One app → Settings → Security → Enable TOTP
       → Copy the TOTP secret shown (or scan the QR code with an authenticator)
"""

import pandas as pd
import requests
from datetime import datetime, timedelta


class AngelOneClient:
    """Wrapper around Angel One SmartAPI."""

    def __init__(self, api_key: str, client_id: str, password: str, totp_secret: str):
        self.api_key     = api_key
        self.client_id   = client_id
        self.password    = password
        self.totp_secret = totp_secret
        self._obj        = None
        self._jwt_token  = None

    def _connect(self):
        """Authenticate and return a connected SmartConnect object."""
        try:
            from SmartApi import SmartConnect
        except ImportError as _e1:
            # Try alternate import path used in some versions
            try:
                from SmartApi.smartConnect import SmartConnect
            except ImportError as _e2:
                raise ImportError(
                    f"Could not import SmartApi. Real errors:\n"
                    f"  SmartApi: {_e1}\n"
                    f"  SmartApi.smartConnect: {_e2}\n\n"
                    f"Run: python -m pip install smartapi-python"
                )
        try:
            import pyotp
        except ImportError:
            raise ImportError(
                "pyotp is not installed.\n"
                "Run: pip install pyotp"
            )

        obj  = SmartConnect(api_key=self.api_key)
        totp = pyotp.TOTP(self.totp_secret).now()
        resp = obj.generateSession(self.client_id, self.password, totp)

        if not resp or resp.get("status") is not True:
            msg = resp.get("message", "Unknown error") if resp else "No response from server"
            raise ConnectionError(f"Angel One login failed: {msg}")

        self._obj = obj
        # Store JWT token for direct REST calls
        self._jwt_token = resp.get("data", {}).get("jwtToken") or getattr(obj, "access_token", None)
        return obj

    def get_holdings(self):
        """
        Fetch current holdings from Angel One.

        Returns
        -------
        (DataFrame | None, error_message | None)

        DataFrame columns (from Angel One API):
            tradingsymbol, symbolname, exchange, isin, t1quantity,
            realisedquantity, quantity, authorisedquantity,
            authoriseddate, averageprice, ltp, close,
            profitandloss, pnlpercentage, totvalue, investedvalue
        """
        try:
            obj  = self._connect()
            resp = obj.holding()

            if not resp or resp.get("status") is not True:
                msg = resp.get("message", "Failed to fetch holdings") if resp else "Empty response"
                return None, msg

            data = resp.get("data", [])
            if not data:
                return pd.DataFrame(), None

            df = pd.DataFrame(data)

            # Coerce numeric columns
            numeric_cols = [
                "quantity", "averageprice", "ltp", "close",
                "profitandloss", "pnlpercentage", "totvalue",
                "investedvalue", "t1quantity", "realisedquantity",
            ]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            return df, None

        except (ImportError, ConnectionError) as e:
            return None, str(e)
        except Exception as e:
            return None, f"Unexpected error: {e}"

    def get_positions(self):
        """
        Fetch today's open positions (intraday / short-term).

        Returns (DataFrame | None, error_message | None)
        """
        try:
            obj  = self._obj or self._connect()
            resp = obj.position()

            if not resp or resp.get("status") is not True:
                msg = resp.get("message", "Failed to fetch positions") if resp else "Empty response"
                return None, msg

            data = resp.get("data", [])
            if not data:
                return pd.DataFrame(), None

            df = pd.DataFrame(data)
            numeric_cols = ["netqty", "avgnetprice", "ltp", "pnl", "netvalue"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            return df, None

        except (ImportError, ConnectionError) as e:
            return None, str(e)
        except Exception as e:
            return None, f"Unexpected error: {e}"

    def get_ledger(self, from_date: str = None, to_date: str = None):
        """
        Fetch ledger statement from Angel One, which includes all fund
        transfers from your bank account.

        Parameters
        ----------
        from_date : str  "YYYY-MM-DD"  (defaults to 2 years ago)
        to_date   : str  "YYYY-MM-DD"  (defaults to today)

        Returns (DataFrame | None, error | None)

        DataFrame has columns:
            date, particulars, amount, transaction_type
            where transaction_type is "CREDIT" (money in) or "DEBIT" (money out)
        """
        try:
            # Ensure we're connected and have a JWT token
            obj = self._obj or self._connect()

            if not self._jwt_token:
                # Try extracting token from object attributes
                for attr in ["access_token", "jwt_token", "jwtToken"]:
                    tok = getattr(obj, attr, None)
                    if tok:
                        self._jwt_token = tok
                        break

            if not self._jwt_token:
                return None, (
                    "Could not retrieve JWT token. "
                    "Angel One ledger requires a valid session token."
                )

            # Date range — default to last 2 years
            if not to_date:
                to_date = datetime.today().strftime("%Y-%m-%d")
            if not from_date:
                from_date = (datetime.today() - timedelta(days=730)).strftime("%Y-%m-%d")

            url = "https://apiconnect.angelbroking.com/rest/secure/angelbroking/portfolio/v1/getLedger"
            headers = {
                "Authorization":    f"Bearer {self._jwt_token}",
                "Content-Type":     "application/json",
                "Accept":           "application/json",
                "X-UserType":       "USER",
                "X-SourceID":       "WEB",
                "X-PrivateKey":     self.api_key,
                "X-ClientLocalIP":  "127.0.0.1",
                "X-ClientPublicIP": "127.0.0.1",
                "X-MACAddress":     "00:00:00:00:00:00",
            }
            params = {"fromDate": from_date, "toDate": to_date}

            resp = requests.get(url, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            if not data.get("status"):
                return None, data.get("message", "Ledger API returned an error")

            entries = data.get("data", [])
            if not entries:
                return pd.DataFrame(), None

            df = pd.DataFrame(entries)

            # Normalise column names (Angel One may vary across versions)
            df.columns = [c.lower().strip() for c in df.columns]

            # Map common column name variants
            rename_map = {
                "transactiondate": "date", "txndate": "date", "postingdate": "date",
                "narration": "particulars", "description": "particulars", "remarks": "particulars",
                "credit": "credit_amt", "debit": "debit_amt",
                "transactiontype": "transaction_type", "txntype": "transaction_type",
            }
            df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

            # Build a clean amount + direction column if separate credit/debit cols exist
            if "credit_amt" in df.columns and "debit_amt" in df.columns:
                df["credit_amt"] = pd.to_numeric(df["credit_amt"], errors="coerce").fillna(0)
                df["debit_amt"]  = pd.to_numeric(df["debit_amt"],  errors="coerce").fillna(0)
                df["amount"]     = df["credit_amt"] - df["debit_amt"]
                df["transaction_type"] = df.apply(
                    lambda r: "CREDIT" if r["credit_amt"] > 0 else "DEBIT", axis=1)
            elif "amount" in df.columns:
                df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

            # Filter to fund-transfer-like entries (bank deposits)
            FUND_KEYWORDS = [
                "payin", "fund", "transfer", "upi", "neft", "rtgs", "imps",
                "bank", "deposit", "receipt", "received",
            ]
            if "particulars" in df.columns:
                mask = df["particulars"].str.lower().str.contains(
                    "|".join(FUND_KEYWORDS), na=False
                )
                df_funds = df[mask].copy()
            else:
                df_funds = df.copy()

            return df_funds, None

        except requests.exceptions.HTTPError as e:
            return None, f"HTTP error fetching ledger: {e}"
        except requests.exceptions.ConnectionError:
            return None, "Network error — could not reach Angel One ledger API"
        except (ImportError, ConnectionError) as e:
            return None, str(e)
        except Exception as e:
            return None, f"Unexpected error: {e}"

    def get_funds(self):
        """
        Fetch current fund balance from Angel One via rmsLimit().

        Returns (dict | None, error | None)

        Useful fields in the returned dict:
            net                  — Total ledger balance (funds added from bank minus withdrawals)
            availablecash        — Cash available to invest right now
            availabledeliverymargin
            utiliseddebits       — Amount currently used / invested
        """
        try:
            obj  = self._obj or self._connect()
            resp = obj.rmsLimit()

            if not resp or resp.get("status") is not True:
                msg = resp.get("message", "Failed to fetch funds") if resp else "Empty response"
                return None, msg

            data = resp.get("data", {})
            if not data:
                return None, "No fund data returned"

            # Coerce all values to float
            cleaned = {}
            for k, v in data.items():
                try:
                    cleaned[k] = float(v) if v not in (None, "") else 0.0
                except (ValueError, TypeError):
                    cleaned[k] = v

            return cleaned, None

        except (ImportError, ConnectionError) as e:
            return None, str(e)
        except Exception as e:
            return None, f"Unexpected error: {e}"

    def get_profile(self):
        """Fetch user profile info. Returns (dict | None, error | None)."""
        try:
            obj  = self._obj or self._connect()
            resp = obj.getProfile(self._refresh_token())
            if not resp or resp.get("status") is not True:
                return None, resp.get("message", "Failed to fetch profile") if resp else "Empty response"
            return resp.get("data", {}), None
        except Exception as e:
            return None, str(e)

    def _refresh_token(self):
        """Return the refresh token stored on the SmartConnect object, if any."""
        if self._obj and hasattr(self._obj, "refresh_token"):
            return self._obj.refresh_token
        return ""
