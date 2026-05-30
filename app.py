"""
Portfolio Manager - Venkat's Investment Dashboard
Supports: Angel One (India), Vested (US), JP Morgan Workplace Solutions (UK)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from pathlib import Path
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Portfolio Manager",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ───────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

SETTINGS_FILE        = DATA_DIR / "settings.json"
US_HOLDINGS_FILE     = DATA_DIR / "us_holdings.json"
UK_HOLDINGS_FILE     = DATA_DIR / "uk_holdings.json"
FUNDS_FILE           = DATA_DIR / "funds.json"
INDIA_FUNDS_FILE     = DATA_DIR / "india_funds.json"
UPLOADS_DIR               = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
VESTED_HOLDINGS_FILE      = UPLOADS_DIR / "vested_holdings.xlsx"
VESTED_TRANSACTIONS_FILE  = UPLOADS_DIR / "vested_transactions.xlsx"
LOANS_FILE                = UPLOADS_DIR / "loans.xlsx"

# ── Helpers ─────────────────────────────────────────────────────────────────────
def load_json(path, default):
    if Path(path).exists():
        with open(path) as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def fmt_inr(val):
    """Format a number as Indian Rupees with ₹ prefix and full number with commas."""
    if val is None:
        return "—"
    try:
        val = float(val)
        return f"₹{val:,.2f}"
    except Exception:
        return "—"

def colour_pnl(val):
    if val is None:
        return "color: grey"
    return "color: #00C875" if val >= 0 else "color: #E2445C"

# ── Custom CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Base ── */
    .stApp { background-color: #0A0E1A; }
    .block-container { padding: 1rem 1rem 2rem 1rem !important; max-width: 100% !important; }

    /* ── Typography ── */
    h1 { font-size: clamp(1.4rem, 5vw, 2rem) !important; color: #F0F2FF !important;
         background: linear-gradient(90deg, #60A5FA, #A78BFA);
         -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    h2 { font-size: clamp(1.1rem, 4vw, 1.5rem) !important; color: #E2E8FF !important; }
    h3 { font-size: clamp(0.95rem, 3vw, 1.15rem) !important; color: #C8D0F0 !important; }
    p, li { color: #9BA3C0; font-size: clamp(0.85rem, 2.5vw, 0.95rem); }

    /* ── Metric cards — colourful gradient borders ── */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #151929 0%, #1C2138 100%);
        border: 1px solid transparent;
        border-radius: 16px;
        padding: 14px 16px;
        position: relative;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    div[data-testid="metric-container"]::before {
        content: "";
        position: absolute; inset: 0;
        border-radius: 16px;
        padding: 1px;
        background: linear-gradient(135deg, #60A5FA44, #A78BFA44, #34D39944);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor; mask-composite: exclude;
        pointer-events: none;
    }
    div[data-testid="metric-container"] label {
        color: #7B84A8 !important;
        font-size: clamp(0.72rem, 2vw, 0.8rem) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="metric-container"] div[data-testid="metric-value"] {
        font-size: clamp(1.1rem, 4vw, 1.5rem) !important;
        font-weight: 700 !important;
        color: #E8EEFF !important;
    }
    div[data-testid="metric-container"] div[data-testid="metric-delta"] {
        font-size: clamp(0.75rem, 2vw, 0.85rem) !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D1120 0%, #111628 100%);
        border-right: 1px solid #1E2540;
    }
    section[data-testid="stSidebar"] .stMarkdown p { color: #6B748F; font-size: 11px; }
    section[data-testid="stSidebar"] h2 {
        background: linear-gradient(90deg, #60A5FA, #A78BFA);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent !important;
    }

    /* ── Nav radio buttons (sidebar) ── */
    div[data-testid="stSidebar"] .stRadio label {
        background: transparent;
        color: #8B93B8 !important;
        border-radius: 10px;
        padding: 8px 12px;
        font-size: 0.9rem;
        transition: all 0.2s;
    }
    div[data-testid="stSidebar"] .stRadio label:hover { background: #1A2040; color: #C8D0F0 !important; }
    div[data-testid="stSidebar"] .stRadio input:checked + div {
        background: linear-gradient(90deg, #1E3A6E, #2D1F5E) !important;
        border-radius: 10px;
        color: #FFFFFF !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(90deg, #2563EB, #7C3AED);
        color: white !important;
        border: none;
        border-radius: 10px;
        padding: 8px 18px;
        font-weight: 600;
        font-size: clamp(0.8rem, 2.5vw, 0.9rem);
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #1D4ED8, #6D28D9);
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.5);
        transform: translateY(-1px);
    }

    /* ── Dataframe ── */
    div[data-testid="stDataFrameContainer"] {
        border-radius: 12px;
        border: 1px solid #1E2540;
        overflow: hidden;
    }

    /* ── Tabs ── */
    div[data-baseweb="tab-list"] {
        background: #131829;
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
    }
    div[data-baseweb="tab"] { color: #7B84A8 !important; border-radius: 8px; }
    div[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(90deg, #1E3A6E, #2D1F5E) !important;
        color: #FFFFFF !important;
    }

    /* ── Expanders ── */
    div[data-testid="stExpander"] {
        background: #131829;
        border: 1px solid #1E2540 !important;
        border-radius: 12px !important;
    }

    /* ── Info / Warning / Success boxes ── */
    div[data-testid="stAlert"] { border-radius: 12px; font-size: 0.88rem; }

    /* ── Divider ── */
    hr { border-color: #1E2540 !important; margin: 1rem 0 !important; }

    /* ── Section headers with colour accent ── */
    .section-india  { color: #FB923C !important; }
    .section-us     { color: #60A5FA !important; }
    .section-uk     { color: #A78BFA !important; }

    /* ── Badges ── */
    .success-badge {
        display: inline-block;
        background: rgba(52,211,153,0.15);
        color: #34D399;
        border: 1px solid rgba(52,211,153,0.3);
        border-radius: 20px; padding: 3px 12px;
        font-size: 12px; font-weight: 600;
    }
    .error-badge {
        display: inline-block;
        background: rgba(239,68,68,0.15);
        color: #EF4444;
        border: 1px solid rgba(239,68,68,0.3);
        border-radius: 20px; padding: 3px 12px;
        font-size: 12px; font-weight: 600;
    }

    /* ── Mobile — stack columns nicely ── */
    @media (max-width: 640px) {
        .block-container { padding: 0.5rem 0.5rem 2rem 0.5rem !important; }
        div[data-testid="metric-container"] { padding: 10px 12px; }
        div[data-testid="metric-container"] div[data-testid="metric-value"] {
            font-size: 1.1rem !important;
        }
        div[data-testid="column"] { min-width: 45% !important; }
    }

    /* ── Input fields ── */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background: #131829 !important;
        border: 1px solid #2A3050 !important;
        border-radius: 8px !important;
        color: #E2E8FF !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Load modules lazily to avoid import errors ─────────────────────────────────
@st.cache_resource
def load_angel_module():
    try:
        from utils.angel_api import AngelOneClient
        return AngelOneClient
    except Exception as e:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_prices_and_fx():
    from utils.price_fetcher import get_fx_rates, get_prices_bulk
    return get_fx_rates(), get_prices_bulk

# ── Load settings — env vars take priority over settings.json ──────────────────
import os as _os

def load_settings():
    """
    Merge settings from two sources (env vars win):
      1. data/settings.json  — used locally
      2. Environment variables — used on Railway / any cloud host
    """
    base = load_json(SETTINGS_FILE, {})
    env_map = {
        "angel_api_key":     "ANGEL_API_KEY",
        "angel_client_id":   "ANGEL_CLIENT_ID",
        "angel_password":    "ANGEL_PASSWORD",
        "angel_totp_secret": "ANGEL_TOTP_SECRET",
    }
    for setting_key, env_key in env_map.items():
        val = _os.environ.get(env_key, "").strip()
        if val:
            base[setting_key] = val
    return base

# ── Session State defaults ──────────────────────────────────────────────────────
if "settings" not in st.session_state:
    st.session_state.settings = load_settings()
if "angel_holdings" not in st.session_state:
    st.session_state.angel_holdings = None
if "angel_error" not in st.session_state:
    st.session_state.angel_error = None
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = None

settings = st.session_state.settings

# ── Sidebar ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Portfolio Manager")
    st.markdown("---")

    nav = st.radio(
        "Navigate",
        ["🏠 Dashboard", "🏦 Funds Added", "🇮🇳 India (Angel One)", "🇺🇸 US (Vested)", "🇬🇧 UK (JP Morgan)", "📋 Trade Analytics", "💳 Loans", "⚙️ Settings"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Quick refresh button
    if st.button("🔄 Refresh Prices", use_container_width=True):
        st.cache_data.clear()
        st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")
        st.rerun()

    if st.session_state.last_refresh:
        st.markdown(f"<p>Last refresh: {st.session_state.last_refresh}</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<p>Prices refresh every 5 minutes.<br>Indian markets: NSE/BSE<br>US: NYSE/NASDAQ<br>UK: LSE</p>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: FUNDS ADDED
# ══════════════════════════════════════════════════════════════════════════════
if nav == "🏦 Funds Added":
    st.title("🏦 Funds Added from Bank")

    funds_data = load_json(FUNDS_FILE, [])

    # ── India — Bank Statement Upload ──────────────────────────────────────────
    st.markdown("### 🇮🇳 Angel One — Funds Sent from Bank")
    st.info("Upload your bank statement (XLS) to calculate how much you have transferred to Angel One. "
            "Any row containing **'Angel One'** in the transaction remarks is counted.")

    import io as _io, subprocess as _sp, tempfile as _tmp, os as _os

    bk_file = st.file_uploader("📄 Bank Statement (.xls or .xlsx)", type=["xls","xlsx"], key="bank_stmt_upload")

    if bk_file:
        with st.spinner("Parsing bank statement…"):
            try:
                raw_bytes = bk_file.read()
                fname     = bk_file.name

                if fname.endswith(".xls"):
                    # Use LibreOffice to convert .xls → .csv
                    with _tmp.NamedTemporaryFile(suffix=".xls", delete=False) as tf:
                        tf.write(raw_bytes)
                        tf_path = tf.name
                    out_dir = _tmp.mkdtemp()
                    _sp.run(
                        ["libreoffice","--headless","--convert-to","csv", tf_path,"--outdir", out_dir],
                        capture_output=True,
                    )
                    csv_path = _os.path.join(out_dir, _os.path.basename(tf_path).replace(".xls",".csv"))
                    df_stmt  = pd.read_csv(csv_path, encoding="utf-8-sig")
                    _os.unlink(tf_path)
                else:
                    df_stmt = pd.read_excel(_io.BytesIO(raw_bytes), engine="openpyxl")

                df_stmt.columns = [c.strip() for c in df_stmt.columns]

                # Find remarks column (flexible naming)
                rem_col = next((c for c in df_stmt.columns
                                if "remark" in c.lower() or "narration" in c.lower()
                                or "description" in c.lower() or "particulars" in c.lower()), None)
                if rem_col is None:
                    st.error("Could not find a remarks/description column in the file.")
                else:
                    mask = df_stmt[rem_col].astype(str).str.contains("angel one|ipo", case=False, na=False)
                    ao   = df_stmt[mask].copy()

                    # Detect debit/credit columns
                    debit_col  = next((c for c in ao.columns if "withdrawal" in c.lower() or "debit" in c.lower()), None)
                    credit_col = next((c for c in ao.columns if "deposit" in c.lower()    or "credit" in c.lower()), None)
                    date_col   = next((c for c in ao.columns if "date" in c.lower() and "transaction" not in c.lower()), None) \
                                 or next((c for c in ao.columns if "date" in c.lower()), None)

                    records = []
                    for _, row in ao.iterrows():
                        w = float(str(row[debit_col]).replace(",","") if debit_col else 0) if debit_col and pd.notna(row[debit_col]) else 0
                        d = float(str(row[credit_col]).replace(",","") if credit_col else 0) if credit_col and pd.notna(row[credit_col]) else 0
                        records.append({
                            "date":    str(row[date_col]) if date_col else "",
                            "remarks": str(row[rem_col]).strip(),
                            "debit":   w,
                            "credit":  d,
                            "amount":  w if w > 0 else d,
                            "type":    "DEBIT" if w > 0 else "CREDIT",
                        })

                    total_sent     = sum(r["debit"]  for r in records)
                    total_returned = sum(r["credit"] for r in records)
                    net_added      = total_sent - total_returned

                    india_funds_data = {
                        "source": "bank_statement",
                        "total_sent":     round(total_sent,     2),
                        "total_returned": round(total_returned, 2),
                        "net_added":      round(net_added,      2),
                        "transactions":   records,
                    }
                    save_json(str(INDIA_FUNDS_FILE), india_funds_data)
                    st.success(f"✅ Found {len(records)} Angel One transactions in the statement")
                    st.rerun()

            except Exception as e:
                st.error(f"Parse error: {e}")

    # ── Show saved India funds data ────────────────────────────────────────────
    india_funds_data = load_json(str(INDIA_FUNDS_FILE), {})

    if india_funds_data:
        total_sent     = india_funds_data.get("total_sent", 0)
        total_returned = india_funds_data.get("total_returned", 0)
        net_added      = india_funds_data.get("net_added", 0)

        fi1, fi2, fi3 = st.columns(3)
        fi1.metric("💸 Total Sent to Angel One", fmt_inr(total_sent),
                   help="Sum of all outgoing bank transfers to Angel One")
        fi2.metric("↩️ Returned from Angel One", fmt_inr(total_returned),
                   help="Dividends / refunds credited back to your bank")
        fi3.metric("📥 Net Funds Added",         fmt_inr(net_added))

        txns = india_funds_data.get("transactions", [])
        if txns:
            with st.expander(f"📋 All {len(txns)} Angel One bank transactions"):
                txn_df = pd.DataFrame(txns)
                txn_df["debit"]  = txn_df["debit"].apply( lambda x: fmt_inr(x) if x > 0 else "—")
                txn_df["credit"] = txn_df["credit"].apply(lambda x: fmt_inr(x) if x > 0 else "—")
                txn_df.columns   = [c.title() for c in txn_df.columns]
                st.dataframe(txn_df[["Date","Remarks","Debit","Credit"]],
                             use_container_width=True, hide_index=True)
    else:
        st.info("Upload a bank statement above to see how much you've sent to Angel One.")

    st.markdown("---")
    st.markdown("### Manual Fund Transfers (Vested & JP Morgan)")
    st.markdown("Vested and JP Morgan don't have fund balance APIs — log those transfers manually below.")

    # ── Add a deposit ──────────────────────────────────────────────────────────
    with st.expander("➕ Add a Fund Transfer", expanded=len(funds_data) == 0):
        with st.form("add_fund"):
            col1, col2, col3 = st.columns(3)
            with col1:
                broker   = st.selectbox("Broker", ["Angel One (India)", "Vested (US)", "JP Morgan (UK)"])
                amount   = st.number_input("Amount", min_value=0.01, step=100.0, format="%.2f")
            with col2:
                currency = st.selectbox("Currency", ["INR", "USD", "GBP"])
                txn_date = st.date_input("Date of Transfer")
            with col3:
                note     = st.text_input("Note (optional)", placeholder="e.g. Monthly top-up")

            if st.form_submit_button("Add Transfer", use_container_width=True):
                funds_data.append({
                    "broker":   broker,
                    "amount":   amount,
                    "currency": currency,
                    "date":     str(txn_date),
                    "note":     note,
                })
                save_json(FUNDS_FILE, funds_data)
                st.success(f"✅ Added {currency} {amount:,.2f} to {broker}")
                st.rerun()

    if funds_data:
        # Fetch FX to convert everything to INR
        with st.spinner("Fetching FX rates..."):
            from utils.price_fetcher import get_fx_rates
            fx      = get_fx_rates()
            usd_inr = fx.get("USD", 84.0)
            gbp_inr = fx.get("GBP", 107.0)

        def to_inr(amount, currency):
            if currency == "INR": return amount
            if currency == "USD": return amount * usd_inr
            if currency == "GBP": return amount * gbp_inr
            return amount

        df_funds = pd.DataFrame(funds_data)
        df_funds["amount"]   = pd.to_numeric(df_funds["amount"], errors="coerce")
        df_funds["inr_value"] = df_funds.apply(lambda r: to_inr(r["amount"], r["currency"]), axis=1)
        df_funds["date"]     = pd.to_datetime(df_funds["date"])

        # ── Summary cards ──────────────────────────────────────────────────────
        total_funds_inr  = df_funds["inr_value"].sum()
        angel_funds_inr  = df_funds[df_funds["broker"] == "Angel One (India)"]["inr_value"].sum()
        vested_funds_inr = df_funds[df_funds["broker"] == "Vested (US)"]["inr_value"].sum()
        jp_funds_inr     = df_funds[df_funds["broker"] == "JP Morgan (UK)"]["inr_value"].sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Funds Added",       fmt_inr(total_funds_inr))
        c2.metric("🇮🇳 Angel One",            fmt_inr(angel_funds_inr))
        c3.metric("🇺🇸 Vested",               fmt_inr(vested_funds_inr))
        c4.metric("🇬🇧 JP Morgan",            fmt_inr(jp_funds_inr))

        st.markdown("---")

        # ── Broker breakdown table ─────────────────────────────────────────────
        st.markdown("### By Broker")
        broker_summary = df_funds.groupby("broker").agg(
            Transfers   = ("amount", "count"),
            Total_INR   = ("inr_value", "sum"),
        ).reset_index()
        broker_summary.columns = ["Broker", "# Transfers", "Total (INR)"]
        broker_summary["Total (INR)"] = broker_summary["Total (INR)"].apply(fmt_inr)
        st.dataframe(broker_summary, use_container_width=True, hide_index=True)

        st.markdown("---")

        # ── Full transaction log ───────────────────────────────────────────────
        st.markdown("### All Transfers")
        display_funds = df_funds.copy()
        display_funds["Amount"] = display_funds.apply(
            lambda r: f"{'₹' if r['currency']=='INR' else '$' if r['currency']=='USD' else '£'}{r['amount']:,.2f}", axis=1)
        display_funds["Value (INR)"] = display_funds["inr_value"].apply(fmt_inr)
        display_funds["Date"] = display_funds["date"].dt.strftime("%d %b %Y")
        display_funds = display_funds[["Date", "Broker", "Amount", "Value (INR)", "note"]].rename(
            columns={"note": "Note"})
        display_funds = display_funds.sort_values("Date", ascending=False)
        st.dataframe(display_funds, use_container_width=True, hide_index=True)

        # ── Delete a transfer ──────────────────────────────────────────────────
        st.markdown("### Remove a Transfer")
        del_options = [
            f"{r['date']} — {r['broker']} — {r['currency']} {float(r['amount']):,.2f}"
            for r in funds_data
        ]
        del_choice = st.selectbox("Select transfer to remove", ["— select —"] + del_options)
        if del_choice != "— select —":
            if st.button("🗑️ Remove this transfer", type="secondary"):
                idx = del_options.index(del_choice)
                funds_data.pop(idx)
                save_json(FUNDS_FILE, funds_data)
                st.success("Removed.")
                st.rerun()

        # ── Cumulative chart ───────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Cumulative Funds Added Over Time")
        chart_df = df_funds.sort_values("date")[["date","inr_value"]].copy()
        chart_df["Cumulative (INR)"] = chart_df["inr_value"].cumsum()
        fig = px.area(
            chart_df, x="date", y="Cumulative (INR)",
            color_discrete_sequence=["#4A90D9"],
        )
        fig.update_layout(
            paper_bgcolor="#1E2130", plot_bgcolor="#1E2130",
            font=dict(color="#C0C4D0"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#2E3250"),
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No fund transfers recorded yet. Use the form above to log your first bank transfer.")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: TRADE ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif nav == "📋 Trade Analytics":
    st.title("📋 Trade Analytics")
    st.markdown("Upload your Angel One reports to analyse your trades and transactions.")

    # ── File uploaders split by market ────────────────────────────────────────
    st.markdown("#### 🇮🇳 Angel One (India) Reports")
    col1, col2, col3 = st.columns(3)
    with col1:
        pnl_file   = st.file_uploader("📄 P&L Statement",      type=["xlsx"], key="pnl_upload")
    with col2:
        trade_file = st.file_uploader("📄 Trade History",       type=["xlsx"], key="trade_upload")
    with col3:
        stmt_file  = st.file_uploader("📄 Account Statement",   type=["xlsx"], key="stmt_upload")

    st.markdown("#### 🇺🇸 Vested (US) Reports")
    col4, col5 = st.columns(2)
    with col4:
        vested_txn_file = st.file_uploader("📄 Vested Transactions", type=["xlsx"], key="vested_txn_upload")
    with col5:
        vested_pnl_file = st.file_uploader("📄 Vested P&L Statement",type=["xlsx"], key="vested_pnl_upload")

    if pnl_file and trade_file:
        st.session_state.ta_pnl_bytes   = pnl_file.read()
        st.session_state.ta_trade_bytes = trade_file.read()
    if stmt_file:
        st.session_state.ta_stmt_bytes  = stmt_file.read()
    if vested_txn_file:
        st.session_state.vested_txn_bytes = vested_txn_file.read()
    if vested_pnl_file:
        st.session_state.vested_pnl_bytes = vested_pnl_file.read()

    has_data        = "ta_pnl_bytes" in st.session_state and "ta_trade_bytes" in st.session_state
    has_vested_data = "vested_txn_bytes" in st.session_state or "vested_pnl_bytes" in st.session_state

    if not has_data and not has_vested_data:
        st.info("Upload your Angel One reports above to see analytics.\n\n"
                "You can also upload Vested reports independently for US portfolio analysis.")
        st.stop()

    # ── Parse files ────────────────────────────────────────────────────────────
    import io
    @st.cache_data(show_spinner=False)
    def parse_trade_data(pnl_bytes, trade_bytes):
        pnl_raw    = pd.read_excel(io.BytesIO(pnl_bytes),   sheet_name="Equity P&L", header=None)
        trades_raw = pd.read_excel(io.BytesIO(trade_bytes), header=None)

        # ── Summary figures ────────────────────────────────────────────────────
        summary = {}
        for _, row in pnl_raw.iterrows():
            key = str(row[0]).strip() if pd.notna(row[0]) else ""
            val = row[1] if pd.notna(row[1]) else None
            for k in ["Total Gross PnL","Net PnL","Intraday Net PnL",
                      "Short Term Net PnL","Total Brokerage","Total STT","Total GST"]:
                if key == k and val is not None:
                    summary[k] = float(val)

        # ── PnL tables ─────────────────────────────────────────────────────────
        def parse_pnl_section(raw, data_start, data_end, trade_type):
            rows = raw.iloc[data_start:data_end].copy()
            df   = rows.iloc[:, :8].copy()
            df.columns = ["Symbol","Company","Quantity","AvgBuyPrice",
                          "BuyValue","AvgSellPrice","SellValue","GrossPnL"]
            df = df[~df["Symbol"].astype(str).str.strip().isin(["Total","nan"])].dropna(subset=["Symbol"])
            for c in ["Quantity","AvgBuyPrice","BuyValue","AvgSellPrice","SellValue","GrossPnL"]:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
            df["TradeType"] = trade_type
            return df

        delivery_df = parse_pnl_section(pnl_raw, 32, 68, "Delivery")
        intraday_df = parse_pnl_section(pnl_raw, 72, 86, "Intraday")
        all_pnl     = pd.concat([delivery_df, intraday_df], ignore_index=True)

        # ── Trade history ──────────────────────────────────────────────────────
        trades_df = trades_raw.iloc[35:].copy()
        col_names = ["Company","BuySell","BuyPrice","SellPrice","Quantity",
                     "Brokerage","GST","STT","SebiTax","ExchangeCharges",
                     "StampDuty","OtherCharges","IPFTCharges","OrderType",
                     "Segment","Exchange","OrderID","TradeID","Date"]
        trades_df.columns = col_names[:len(trades_df.columns)]
        trades_df = trades_df.dropna(subset=["Company"])
        trades_df = trades_df[trades_df["Company"].astype(str).str.strip().ne("")]
        for c in ["BuyPrice","SellPrice","Quantity","Brokerage","GST","STT"]:
            trades_df[c] = pd.to_numeric(trades_df[c], errors="coerce").fillna(0)
        trades_df["Date"] = pd.to_datetime(trades_df["Date"], errors="coerce")

        buy_df  = trades_df[trades_df["BuySell"] == "Buy"]
        sell_df = trades_df[trades_df["BuySell"] == "Sell"]

        # Per-company stats
        buy_stats   = buy_df.groupby("Company").apply(
            lambda g: pd.Series({"BuyTrades": len(g), "BuyValue": (g["BuyPrice"]*g["Quantity"]).sum()})
        ).reset_index()
        sell_stats  = sell_df.groupby("Company").apply(
            lambda g: pd.Series({"SellTrades": len(g), "SellValue": (g["SellPrice"]*g["Quantity"]).sum()})
        ).reset_index()
        charge_stats = trades_df.groupby("Company").agg(
            Charges=("Brokerage","sum")
        ).reset_index()

        company_stats = buy_stats.merge(sell_stats,   on="Company", how="outer").fillna(0)
        company_stats = company_stats.merge(charge_stats, on="Company", how="left").fillna(0)
        company_stats["BuyTrades"]  = company_stats["BuyTrades"].astype(int)
        company_stats["SellTrades"] = company_stats["SellTrades"].astype(int)

        pnl_by_company = all_pnl.groupby("Company").agg(
            GrossPnL=("GrossPnL","sum"),
        ).reset_index()
        final = company_stats.merge(pnl_by_company, on="Company", how="left")
        final["GrossPnL"] = final["GrossPnL"].fillna(0)
        final["NetPnL"]   = final["GrossPnL"] - final["Charges"]
        final = final.sort_values("BuyValue", ascending=False).reset_index(drop=True)

        # Totals
        total_invested  = (buy_df["BuyPrice"]  * buy_df["Quantity"]).sum()
        total_recovered = (sell_df["SellPrice"] * sell_df["Quantity"]).sum()
        total_charges   = trades_df["Brokerage"].sum() + trades_df["GST"].sum() + trades_df["STT"].sum()
        gross_pnl       = summary.get("Total Gross PnL", 0)
        net_pnl         = summary.get("Net PnL",         0)

        totals = {
            "total_invested":  total_invested,
            "total_recovered": total_recovered,
            "total_charges":   total_charges,
            "gross_pnl":       gross_pnl,
            "net_pnl":         net_pnl,
            "intraday_pnl":    summary.get("Intraday Net PnL",   0),
            "delivery_pnl":    summary.get("Short Term Net PnL", 0),
            "total_trades":    len(trades_df),
            "buy_trades":      len(buy_df),
            "sell_trades":     len(sell_df),
        }
        return final, totals, trades_df

    if has_data:
        with st.spinner("Parsing your files…"):
            company_df, totals, trades_df = parse_trade_data(
                st.session_state.ta_pnl_bytes,
                st.session_state.ta_trade_bytes
            )

        # ── Summary metrics ────────────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Total Funds Invested",   fmt_inr(totals["total_invested"]))
        c2.metric("💵 Total Recovered (Sells)",fmt_inr(totals["total_recovered"]))
        c3.metric("📊 Gross P&L",             fmt_inr(totals["gross_pnl"]),
                  f"{totals['gross_pnl']/totals['total_invested']*100:+.2f}%" if totals["total_invested"] else "",
                  delta_color="normal" if totals["gross_pnl"] >= 0 else "inverse")
        c4.metric("🏦 Net P&L (after charges)",fmt_inr(totals["net_pnl"]),
                  delta_color="normal" if totals["net_pnl"] >= 0 else "inverse")

        st.markdown("---")

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Delivery P&L",  fmt_inr(totals["delivery_pnl"]),
                  delta_color="normal" if totals["delivery_pnl"] >= 0 else "inverse")
        c6.metric("Intraday P&L",  fmt_inr(totals["intraday_pnl"]),
                  delta_color="normal" if totals["intraday_pnl"] >= 0 else "inverse")
        c7.metric("Total Trades",  f"{totals['total_trades']}",
                  f"{totals['buy_trades']} buy · {totals['sell_trades']} sell")
        c8.metric("Total Charges", fmt_inr(totals["total_charges"]))

        st.markdown("---")

        # ── Top Gainers / Losers ────────────────────────────────────────────────────
        st.markdown("### Top Gainers & Losers")
        g_col, l_col = st.columns(2)

        with g_col:
            gainers = company_df[company_df["GrossPnL"] > 0].nlargest(8, "GrossPnL")
            if not gainers.empty:
                fig_g = go.Figure(go.Bar(
                    x=gainers["GrossPnL"], y=gainers["Company"],
                    orientation="h", marker_color="#22c55e",
                    text=gainers["GrossPnL"].apply(lambda x: f"₹{x:+,.0f}"),
                    textposition="outside",
                ))
                fig_g.update_layout(
                    title="🟢 Top Gainers", paper_bgcolor="#1E2130", plot_bgcolor="#1E2130",
                    font=dict(color="#C0C4D0"), margin=dict(l=10,r=60,t=40,b=10),
                    height=320, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
                )
                st.plotly_chart(fig_g, use_container_width=True)

        with l_col:
            losers = company_df[company_df["GrossPnL"] < 0].nsmallest(8, "GrossPnL")
            if not losers.empty:
                fig_l = go.Figure(go.Bar(
                    x=losers["GrossPnL"], y=losers["Company"],
                    orientation="h", marker_color="#ef4444",
                    text=losers["GrossPnL"].apply(lambda x: f"₹{x:+,.0f}"),
                    textposition="outside",
                ))
                fig_l.update_layout(
                    title="🔴 Top Losers", paper_bgcolor="#1E2130", plot_bgcolor="#1E2130",
                    font=dict(color="#C0C4D0"), margin=dict(l=10,r=60,t=40,b=10),
                    height=320, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
                )
                st.plotly_chart(fig_l, use_container_width=True)

        st.markdown("---")

        # ── Company-wise table ──────────────────────────────────────────────────────
        st.markdown("### Company-wise Breakdown")
        search = st.text_input("🔍 Search company", placeholder="e.g. TATA, INFY…", label_visibility="collapsed")

        display_df = company_df.copy()
        if search:
            display_df = display_df[display_df["Company"].str.upper().str.contains(search.upper())]

        display_df["Funds Invested"] = display_df["BuyValue"].apply(fmt_inr)
        display_df["Gross P&L"]      = display_df["GrossPnL"].apply(lambda x: f"₹{x:+,.2f}")
        display_df["Charges"]        = display_df["Charges"].apply(lambda x: f"₹{x:,.2f}")
        display_df["Net P&L"]        = display_df["NetPnL"].apply(lambda x: f"₹{x:+,.2f}")

        st.dataframe(
            display_df[["Company","BuyTrades","SellTrades","Funds Invested","Gross P&L","Charges","Net P&L"]].rename(
                columns={"BuyTrades":"Buy Trades","SellTrades":"Sell Trades"}
            ),
            use_container_width=True, hide_index=True
        )

        st.markdown("---")

        # ── Monthly P&L trend ───────────────────────────────────────────────────────
        st.markdown("### Monthly Trade Activity")
        if "Date" in trades_df.columns and trades_df["Date"].notna().any():
            trades_df["Month"] = trades_df["Date"].dt.to_period("M").astype(str)
            buy_monthly  = trades_df[trades_df["BuySell"]=="Buy"].groupby("Month").apply(
                lambda g: (g["BuyPrice"]*g["Quantity"]).sum()).reset_index(name="BuyValue")
            sell_monthly = trades_df[trades_df["BuySell"]=="Sell"].groupby("Month").apply(
                lambda g: (g["SellPrice"]*g["Quantity"]).sum()).reset_index(name="SellValue")
            monthly = buy_monthly.merge(sell_monthly, on="Month", how="outer").fillna(0).sort_values("Month")

            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(name="Buy Value",  x=monthly["Month"], y=monthly["BuyValue"],
                                   marker_color="#3b82f6"))
            fig_m.add_trace(go.Bar(name="Sell Value", x=monthly["Month"], y=monthly["SellValue"],
                                   marker_color="#22c55e"))
            fig_m.update_layout(
                barmode="group", paper_bgcolor="#1E2130", plot_bgcolor="#1E2130",
                font=dict(color="#C0C4D0"), legend=dict(bgcolor="#1E2130"),
                margin=dict(l=0,r=0,t=20,b=0),
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#2E3250"),
                height=300,
            )
            st.plotly_chart(fig_m, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  ACCOUNT STATEMENT SECTION
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("## 📒 Account Statement — Transaction Analysis")

    if "ta_stmt_bytes" not in st.session_state:
        st.info("Upload your **Account Statement (.xlsx)** above to see transaction-wise analysis.")
    else:
        import io as _io

        @st.cache_data(show_spinner=False)
        def parse_statement(stmt_bytes):
            raw = pd.read_excel(_io.BytesIO(stmt_bytes), sheet_name="Broking Ledger", header=None)

            # Summary figures from header rows
            opening  = 0.0
            closing  = 0.0
            t_credit = 0.0
            t_debit  = 0.0
            for _, row in raw.iterrows():
                r = [str(v).strip() if pd.notna(v) else "" for v in row]
                if r[0] == "Opening Balance":
                    try: opening = float(r[1])
                    except: pass
                if "Closing Balance" in r:
                    idx = r.index("Closing Balance")
                    try: closing = float(r[idx+1])
                    except: pass
                if r[0] == "Total Credit":
                    try: t_credit = float(r[1])
                    except: pass
                if r[0] == "Total Debit":
                    try: t_debit = float(r[1])
                    except: pass

            # Transaction rows start after the header row "Transaction Date Segment..."
            header_idx = None
            for i, row in raw.iterrows():
                if str(row[0]).strip() == "Transaction":
                    header_idx = i
                    break

            txn_df = raw.iloc[header_idx+1:].copy()
            txn_df.columns = ["Transaction","Date","Segment","Voucher","Debit","Credit","Balance"]
            txn_df = txn_df.dropna(subset=["Transaction"])
            txn_df = txn_df[txn_df["Transaction"].astype(str).str.strip().ne("")]
            txn_df["Transaction"] = txn_df["Transaction"].astype(str).str.strip()
            for c in ["Debit","Credit","Balance"]:
                txn_df[c] = pd.to_numeric(txn_df[c], errors="coerce").fillna(0)
            txn_df["Date"] = pd.to_datetime(txn_df["Date"], errors="coerce")
            txn_df = txn_df[txn_df["Date"].notna()].copy()
            txn_df["Month"] = txn_df["Date"].dt.to_period("M").astype(str)

            # Charges sheet
            charges_raw = pd.read_excel(_io.BytesIO(stmt_bytes), sheet_name="Charges", header=None)
            charges_summary = {}
            for _, row in charges_raw.iterrows():
                key = str(row[0]).strip() if pd.notna(row[0]) else ""
                val = row[1] if pd.notna(row[1]) else 0
                for k in ["Total DP Charges","Total Pledge/Unpledge Charges",
                           "Total CUSPA Sell-off Charges","Total Interest Charges"]:
                    if key == k:
                        try: charges_summary[k] = float(val)
                        except: pass

            return txn_df, {"opening": opening, "closing": closing,
                            "total_credit": t_credit, "total_debit": t_debit}, charges_summary

        with st.spinner("Parsing statement…"):
            txn_df, ledger_summary, charges_summary = parse_statement(st.session_state.ta_stmt_bytes)

        # ── Ledger summary cards ───────────────────────────────────────────────
        funds_added_total = txn_df[txn_df["Transaction"] == "Funds Added"]["Credit"].sum()
        trades_debit      = txn_df[txn_df["Transaction"] == "Trades Executed"]["Debit"].sum()
        trades_credit     = txn_df[txn_df["Transaction"] == "Trades Executed"]["Credit"].sum()
        total_charges_stmt = (txn_df[~txn_df["Transaction"].isin(["Funds Added","Trades Executed",
                              "Quarterly Settlement","REVERSED DEMAT ACCOUNT MONTHLY MAINTENANACE CHARGES DT : JAN 1 2026",
                              "Msg"])]["Debit"].sum())

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🏦 Funds Added from Bank",  fmt_inr(funds_added_total))
        c2.metric("📤 Total Trade Spend",       fmt_inr(trades_debit))
        c3.metric("📥 Total Trade Receipts",    fmt_inr(trades_credit))
        c4.metric("💸 Closing Balance",         fmt_inr(ledger_summary["closing"]))

        st.markdown("---")

        # ── Transaction type summary table ────────────────────────────────────
        st.markdown("### By Transaction Type")
        grp = txn_df.groupby("Transaction").agg(
            Count   = ("Date",   "count"),
            Debit   = ("Debit",  "sum"),
            Credit  = ("Credit", "sum"),
        ).reset_index().sort_values("Debit", ascending=False)
        grp["Net (Credit − Debit)"] = grp["Credit"] - grp["Debit"]
        disp_grp = grp.copy()
        for col in ["Debit","Credit","Net (Credit − Debit)"]:
            disp_grp[col] = disp_grp[col].apply(fmt_inr)
        disp_grp.columns = ["Transaction Type","# Entries","Total Debit","Total Credit","Net"]
        st.dataframe(disp_grp, use_container_width=True, hide_index=True)

        st.markdown("---")

        # ── Two charts side by side ────────────────────────────────────────────
        ch1, ch2 = st.columns(2)

        with ch1:
            st.markdown("### Monthly Funds Added")
            monthly_funds = (
                txn_df[txn_df["Transaction"] == "Funds Added"]
                .groupby("Month")["Credit"].sum()
                .reset_index()
                .sort_values("Month")
            )
            if not monthly_funds.empty:
                fig_fa = px.bar(monthly_funds, x="Month", y="Credit",
                                color_discrete_sequence=["#4A90D9"],
                                labels={"Credit":"Amount (INR)","Month":"Month"})
                fig_fa.update_layout(
                    paper_bgcolor="#1E2130", plot_bgcolor="#1E2130",
                    font=dict(color="#C0C4D0"),
                    xaxis=dict(showgrid=False, tickangle=-45),
                    yaxis=dict(showgrid=True, gridcolor="#2E3250"),
                    margin=dict(l=0,r=0,t=10,b=0), height=280,
                )
                st.plotly_chart(fig_fa, use_container_width=True)

        with ch2:
            st.markdown("### Monthly Trade Activity (Debit vs Credit)")
            monthly_trades = (
                txn_df[txn_df["Transaction"] == "Trades Executed"]
                .groupby("Month")[["Debit","Credit"]].sum()
                .reset_index().sort_values("Month")
            )
            if not monthly_trades.empty:
                fig_tr = go.Figure()
                fig_tr.add_trace(go.Bar(name="Trade Spend",    x=monthly_trades["Month"],
                                        y=monthly_trades["Debit"],  marker_color="#ef4444"))
                fig_tr.add_trace(go.Bar(name="Trade Receipts", x=monthly_trades["Month"],
                                        y=monthly_trades["Credit"], marker_color="#22c55e"))
                fig_tr.update_layout(
                    barmode="group", paper_bgcolor="#1E2130", plot_bgcolor="#1E2130",
                    font=dict(color="#C0C4D0"), legend=dict(bgcolor="#1E2130"),
                    xaxis=dict(showgrid=False, tickangle=-45),
                    yaxis=dict(showgrid=True, gridcolor="#2E3250"),
                    margin=dict(l=0,r=0,t=10,b=0), height=280,
                )
                st.plotly_chart(fig_tr, use_container_width=True)

        st.markdown("---")

        # ── Running balance chart ──────────────────────────────────────────────
        st.markdown("### Account Balance Over Time")
        bal_df = txn_df[txn_df["Balance"] != 0].sort_values("Date")
        if not bal_df.empty:
            fig_bal = px.area(bal_df, x="Date", y="Balance",
                              color_discrete_sequence=["#4A90D9"],
                              labels={"Balance":"Running Balance (INR)"})
            fig_bal.add_hline(y=0, line_color="#6b7280", line_dash="dash")
            fig_bal.update_layout(
                paper_bgcolor="#1E2130", plot_bgcolor="#1E2130",
                font=dict(color="#C0C4D0"),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#2E3250"),
                margin=dict(l=0,r=0,t=10,b=0), height=280,
            )
            st.plotly_chart(fig_bal, use_container_width=True)

        st.markdown("---")

        # ── Charges breakdown ──────────────────────────────────────────────────
        st.markdown("### Charges Breakdown")
        cc1, cc2, cc3, cc4 = st.columns(4)
        cc1.metric("DP Charges",              fmt_inr(charges_summary.get("Total DP Charges", 0)))
        cc2.metric("Pledge/Unpledge",         fmt_inr(charges_summary.get("Total Pledge/Unpledge Charges", 0)))
        cc3.metric("Interest Charges",        fmt_inr(charges_summary.get("Total Interest Charges", 0)))
        cc4.metric("CUSPA Sell-off",          fmt_inr(charges_summary.get("Total CUSPA Sell-off Charges", 0)))

        # DP charges detail table
        dp_rows = txn_df[txn_df["Transaction"] == "DP Charges"][["Date","Debit","Segment"]].copy()
        if not dp_rows.empty:
            with st.expander(f"📋 DP Charges detail ({len(dp_rows)} entries)"):
                dp_rows["Date"]  = dp_rows["Date"].dt.strftime("%d %b %Y")
                dp_rows["Debit"] = dp_rows["Debit"].apply(fmt_inr)
                dp_rows.columns  = ["Date","Amount","Segment"]
                st.dataframe(dp_rows, use_container_width=True, hide_index=True)

        # ── Full transaction log ───────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Full Transaction Log")
        txn_filter = st.multiselect(
            "Filter by transaction type",
            options=sorted(txn_df["Transaction"].unique()),
            default=sorted(txn_df["Transaction"].unique()),
        )
        filtered_txn = txn_df[txn_df["Transaction"].isin(txn_filter)].copy()
        filtered_txn["Date"]    = filtered_txn["Date"].dt.strftime("%d %b %Y")
        filtered_txn["Debit"]   = filtered_txn["Debit"].apply(fmt_inr)
        filtered_txn["Credit"]  = filtered_txn["Credit"].apply(fmt_inr)
        filtered_txn["Balance"] = filtered_txn["Balance"].apply(
            lambda x: f"₹{float(x):+,.2f}" if x != 0 else "—")
        st.dataframe(
            filtered_txn[["Date","Transaction","Debit","Credit","Balance","Segment","Voucher"]],
            use_container_width=True, hide_index=True
        )


    # ══════════════════════════════════════════════════════════════════════════
    #  VESTED (US) SECTION
    # ══════════════════════════════════════════════════════════════════════════
    if has_vested_data:
        st.markdown("---")
        st.markdown("## 🇺🇸 Vested (US) Portfolio Analytics")

        import io as _io

        @st.cache_data(show_spinner=False)
        def parse_vested_data(txn_bytes, pnl_bytes):
            result = {
                "transfers": pd.DataFrame(),
                "trades": pd.DataFrame(),
                "income": pd.DataFrame(),
                "unrealized": pd.DataFrame(),
                "realized": pd.DataFrame(),
                "errors": [],
            }

            # ── Transactions file ──────────────────────────────────────────────
            if txn_bytes:
                try:
                    xl = pd.ExcelFile(_io.BytesIO(txn_bytes))

                    # Transfers sheet
                    if "Transfers" in xl.sheet_names:
                        df = xl.parse("Transfers")
                        df.columns = [c.strip() for c in df.columns]
                        amt_col = [c for c in df.columns if "Cash Amount" in c]
                        if amt_col:
                            df["amount_usd"] = pd.to_numeric(df[amt_col[0]], errors="coerce").fillna(0)
                        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                        result["transfers"] = df

                    # Trades sheet
                    if "Trades" in xl.sheet_names:
                        df = xl.parse("Trades")
                        df.columns = [c.strip() for c in df.columns]
                        for col in ["Cash Amount (in USD)", "Price Per Share (in USD)",
                                    "Commission Charges (in USD)", "Quantity"]:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
                        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                        result["trades"] = df

                    # Income sheet
                    if "Income" in xl.sheet_names:
                        df = xl.parse("Income")
                        df.columns = [c.strip() for c in df.columns]
                        amt_col = [c for c in df.columns if "Gross Cash" in c or "Amount" in c]
                        if amt_col:
                            df["amount_usd"] = pd.to_numeric(df[amt_col[0]], errors="coerce").fillna(0)
                        result["income"] = df

                except Exception as e:
                    result["errors"].append(f"Transactions parse error: {e}")

            # ── P&L file ───────────────────────────────────────────────────────
            if pnl_bytes:
                try:
                    xl = pd.ExcelFile(_io.BytesIO(pnl_bytes))

                    unreal_sheet = next((s for s in xl.sheet_names if "Unrealized" in s and "Summary" in s), None)
                    real_sheet   = next((s for s in xl.sheet_names if "Realized" in s and "Summary" in s), None)

                    if unreal_sheet:
                        df = xl.parse(unreal_sheet)
                        df.columns = [c.strip() for c in df.columns]
                        for col in df.columns:
                            if col != "Security":
                                df[col] = pd.to_numeric(df[col], errors="coerce")
                        result["unrealized"] = df

                    if real_sheet:
                        df = xl.parse(real_sheet)
                        df.columns = [c.strip() for c in df.columns]
                        for col in df.columns:
                            if col != "Security":
                                df[col] = pd.to_numeric(df[col], errors="coerce")
                        result["realized"] = df

                except Exception as e:
                    result["errors"].append(f"P&L parse error: {e}")

            return result

        vdata = parse_vested_data(
            st.session_state.get("vested_txn_bytes"),
            st.session_state.get("vested_pnl_bytes"),
        )

        for err in vdata["errors"]:
            st.warning(f"⚠️ {err}")

        fx = st.session_state.get("fx_rates", {"USD": 84.0, "INR": 1.0})
        usd_to_inr = fx.get("USD", 84.0)

        # ── Summary metrics ────────────────────────────────────────────────────
        total_deposited = vdata["transfers"]["amount_usd"].sum() if not vdata["transfers"].empty else 0.0

        realized_pnl = 0.0
        if not vdata["realized"].empty:
            pnl_col = [c for c in vdata["realized"].columns if "Profit/Loss (USD)" in c]
            if pnl_col:
                realized_pnl = float(vdata["realized"][pnl_col[0]].sum())

        unrealized_pnl = 0.0
        market_value   = 0.0
        cost_basis_open = 0.0
        if not vdata["unrealized"].empty:
            pnl_col = [c for c in vdata["unrealized"].columns if "Profit/Loss (USD)" in c]
            mv_col  = [c for c in vdata["unrealized"].columns if "Market Value" in c]
            cb_col  = [c for c in vdata["unrealized"].columns if "Cost Basis" in c]
            if pnl_col:
                unrealized_pnl = float(vdata["unrealized"][pnl_col[0]].sum())
            if mv_col:
                market_value = float(vdata["unrealized"][mv_col[0]].sum())
            if cb_col:
                cost_basis_open = float(vdata["unrealized"][cb_col[0]].sum())

        dividend_income = vdata["income"]["amount_usd"].sum() if not vdata["income"].empty else 0.0
        net_pnl = realized_pnl + unrealized_pnl + dividend_income

        def fmt_usd(v):
            sign = "+" if v > 0 else ""
            return f"{sign}${v:,.2f}"

        def fmt_usd_plain(v):
            return f"${v:,.2f}"

        vm1, vm2, vm3, vm4, vm5 = st.columns(5)
        vm1.metric("💵 Total Deposited",    fmt_usd_plain(total_deposited),
                   f"≈ {fmt_inr(total_deposited * usd_to_inr)}")
        vm2.metric("📈 Unrealized P&L",     fmt_usd(unrealized_pnl),
                   f"≈ {fmt_inr(unrealized_pnl * usd_to_inr)}",
                   delta_color="normal")
        vm3.metric("✅ Realized P&L",       fmt_usd(realized_pnl),
                   f"≈ {fmt_inr(realized_pnl * usd_to_inr)}",
                   delta_color="normal")
        vm4.metric("💰 Dividend Income",    fmt_usd_plain(dividend_income),
                   f"≈ {fmt_inr(dividend_income * usd_to_inr)}")
        vm5.metric("🏆 Net P&L",            fmt_usd(net_pnl),
                   f"≈ {fmt_inr(net_pnl * usd_to_inr)}",
                   delta_color="normal")

        st.markdown("---")

        # ── Open Positions ─────────────────────────────────────────────────────
        if not vdata["unrealized"].empty:
            st.markdown("### 📂 Open Positions")
            udf = vdata["unrealized"].copy()
            pnl_col = [c for c in udf.columns if "Profit/Loss (USD)" in c and "%" not in c]
            pct_col = [c for c in udf.columns if "Profit/Loss (%)" in c]
            mv_col  = [c for c in udf.columns if "Market Value" in c]
            cb_col  = [c for c in udf.columns if "Cost Basis" in c]

            display_cols = ["Security", "Quantity"]
            rename_map = {"Security": "Ticker"}
            if cb_col:
                udf["Cost (USD)"]   = udf[cb_col[0]].map(lambda x: f"${x:,.2f}")
                display_cols.append("Cost (USD)")
            if mv_col:
                udf["Value (USD)"]  = udf[mv_col[0]].map(lambda x: f"${x:,.2f}")
                display_cols.append("Value (USD)")
            if pnl_col:
                udf["P&L (USD)"]    = udf[pnl_col[0]].map(lambda x: f"+${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}")
                display_cols.append("P&L (USD)")
            if pct_col:
                udf["P&L (%)"]      = udf[pct_col[0]].map(lambda x: f"+{x:.2f}%" if x >= 0 else f"{x:.2f}%")
                display_cols.append("P&L (%)")
            if mv_col:
                udf["Value (INR)"]  = udf[mv_col[0]].map(lambda x: fmt_inr(x * usd_to_inr))
                display_cols.append("Value (INR)")

            st.dataframe(udf[display_cols].rename(columns=rename_map),
                         use_container_width=True, hide_index=True)

            # Unrealized P&L bar chart
            if pnl_col:
                fig_u = px.bar(
                    udf.sort_values(pnl_col[0], ascending=False),
                    x="Security", y=pnl_col[0],
                    color=pnl_col[0],
                    color_continuous_scale=["#EF4444","#F97316","#22C55E"],
                    labels={pnl_col[0]: "Unrealized P&L (USD)", "Security": "Ticker"},
                    title="Unrealized P&L per Stock (USD)",
                )
                fig_u.update_layout(
                    paper_bgcolor="#1E2130", plot_bgcolor="#1E2130",
                    font=dict(color="#C0C4D0"),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="#2E3250"),
                    coloraxis_showscale=False,
                    margin=dict(l=0,r=0,t=40,b=0), height=300,
                )
                st.plotly_chart(fig_u, use_container_width=True)

        # ── Realized P&L ───────────────────────────────────────────────────────
        if not vdata["realized"].empty:
            st.markdown("---")
            st.markdown("### 📊 Realized P&L — Closed Positions")
            rdf = vdata["realized"].copy()
            pnl_col = [c for c in rdf.columns if "Profit/Loss (USD)" in c and "%" not in c]
            pct_col = [c for c in rdf.columns if "Profit/Loss (%)" in c]
            proc_col = [c for c in rdf.columns if "Proceeds" in c]
            cb_col   = [c for c in rdf.columns if "Cost Basis" in c]

            if pnl_col:
                rdf_sorted = rdf.sort_values(pnl_col[0], ascending=False)

                # Top gainers / losers side-by-side
                top_n  = min(10, len(rdf_sorted))
                gainers = rdf_sorted.head(top_n)
                losers  = rdf_sorted.tail(top_n).sort_values(pnl_col[0])

                gc, lc = st.columns(2)
                with gc:
                    st.markdown("**🏆 Top Gainers**")
                    fig_g = px.bar(gainers, x="Security", y=pnl_col[0],
                                   color_discrete_sequence=["#22C55E"],
                                   labels={pnl_col[0]: "P&L (USD)"})
                    fig_g.update_layout(
                        paper_bgcolor="#1E2130", plot_bgcolor="#1E2130",
                        font=dict(color="#C0C4D0"),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor="#2E3250"),
                        margin=dict(l=0,r=0,t=10,b=0), height=260,
                    )
                    st.plotly_chart(fig_g, use_container_width=True)

                with lc:
                    st.markdown("**📉 Top Losers**")
                    fig_l = px.bar(losers, x="Security", y=pnl_col[0],
                                   color_discrete_sequence=["#EF4444"],
                                   labels={pnl_col[0]: "P&L (USD)"})
                    fig_l.update_layout(
                        paper_bgcolor="#1E2130", plot_bgcolor="#1E2130",
                        font=dict(color="#C0C4D0"),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor="#2E3250"),
                        margin=dict(l=0,r=0,t=10,b=0), height=260,
                    )
                    st.plotly_chart(fig_l, use_container_width=True)

                # Full realized table
                with st.expander(f"📋 All closed positions ({len(rdf)} stocks)"):
                    rdf_disp = rdf.copy()
                    if proc_col:
                        rdf_disp["Proceeds"]   = rdf_disp[proc_col[0]].map(lambda x: f"${x:,.2f}")
                    if cb_col:
                        rdf_disp["Cost Basis"] = rdf_disp[cb_col[0]].map(lambda x: f"${x:,.2f}")
                    rdf_disp["P&L (USD)"] = rdf_disp[pnl_col[0]].map(
                        lambda x: f"+${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}")
                    if pct_col:
                        rdf_disp["P&L (%)"] = rdf_disp[pct_col[0]].map(
                            lambda x: f"+{x:.2f}%" if x >= 0 else f"{x:.2f}%")
                    show_cols = ["Security", "Quantity"]
                    for c in ["Proceeds","Cost Basis","P&L (USD)","P&L (%)"]:
                        if c in rdf_disp.columns:
                            show_cols.append(c)
                    st.dataframe(rdf_disp[show_cols], use_container_width=True, hide_index=True)

        # ── Trade activity ─────────────────────────────────────────────────────
        if not vdata["trades"].empty:
            st.markdown("---")
            st.markdown("### 🔄 Trade Activity by Stock")
            tdf = vdata["trades"].copy()
            act_col  = "Activity"
            name_col = "Name" if "Name" in tdf.columns else "Ticker"
            tick_col = "Ticker"

            # Group by Ticker
            grp = tdf.groupby(tick_col)
            rows = []
            for ticker, grp_df in grp:
                name = grp_df[name_col].iloc[0] if name_col in grp_df.columns else ticker
                buys  = grp_df[grp_df[act_col] == "Buy"]
                sells = grp_df[grp_df[act_col] == "Sell"]
                cash_col = "Cash Amount (in USD)"
                buy_val  = buys[cash_col].sum()  if cash_col in buys.columns  else 0
                sell_val = sells[cash_col].sum() if cash_col in sells.columns else 0
                rows.append({
                    "Ticker": ticker,
                    "Company": name[:30] + "…" if len(name) > 30 else name,
                    "Buy Trades":  len(buys),
                    "Sell Trades": len(sells),
                    "Buy Value ($)":  f"${buy_val:,.2f}",
                    "Sell Value ($)": f"${sell_val:,.2f}",
                })
            act_df = pd.DataFrame(rows).sort_values("Buy Trades", ascending=False)
            st.dataframe(act_df, use_container_width=True, hide_index=True)

        # ── Deposits / Transfers ───────────────────────────────────────────────
        if not vdata["transfers"].empty:
            st.markdown("---")
            st.markdown("### 🏦 Fund Transfers (Deposits)")
            trf = vdata["transfers"].copy()
            trf["Date"] = trf["Date"].dt.strftime("%d %b %Y")
            trf["Amount (USD)"] = trf["amount_usd"].map(lambda x: f"${x:,.2f}")
            trf["Amount (INR)"] = trf["amount_usd"].map(lambda x: fmt_inr(x * usd_to_inr))
            show_cols = ["Date", "Activity", "Amount (USD)", "Amount (INR)"]
            show_cols = [c for c in show_cols if c in trf.columns]
            st.dataframe(trf[show_cols], use_container_width=True, hide_index=True)

            st.success(f"**Total Deposited: ${total_deposited:,.2f}** "
                       f"(≈ {fmt_inr(total_deposited * usd_to_inr)})")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: LOANS
# ══════════════════════════════════════════════════════════════════════════════
elif nav == "💳 Loans":
    st.title("💳 Loan Dashboard")

    # ── Helper to load & clean loans ────────────────────────────────────────
    def load_loans(file_path):
        try:
            xl  = pd.ExcelFile(str(file_path))
            # Try header=0 first; if columns look numeric try header=None
            df  = xl.parse(xl.sheet_names[0], header=0)
            df.columns = [str(c).strip() for c in df.columns]

            # If pandas missed the header (columns are integers), re-read with no header
            if all(str(c).isdigit() for c in df.columns):
                df = xl.parse(xl.sheet_names[0], header=None)
                df.columns = [str(c).strip() for c in df.iloc[0]]
                df = df.iloc[1:].reset_index(drop=True)

            # Rename to standard names regardless of original casing
            col_map = {}
            for c in df.columns:
                cl = str(c).lower()
                if "bank" in cl or "name" in cl:
                    col_map[c] = "Bank"
                elif "amount" in cl or "outstanding" in cl or "principal" in cl:
                    col_map[c] = "Amount"
                elif "emi" in cl or "monthly" in cl or "instalment" in cl:
                    col_map[c] = "EMI"
            df = df.rename(columns=col_map)

            # Keep only rows that have Bank, Amount, EMI
            for col in ["Bank", "Amount", "EMI"]:
                if col not in df.columns:
                    return None, f"Column '{col}' not found. Columns found: {list(df.columns)}"

            # Fix malformed numbers like '2.377.63'; return None for non-numeric strings
            def clean_num(v):
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    return None
                if isinstance(v, (int, float)):
                    return float(v)
                s = str(v).strip().replace(",", "")
                if not s or s.lower() in ("amount", "emi", "nan", "-", "n/a"):
                    return None
                parts = s.split(".")
                if len(parts) > 2:          # e.g. '2.377.63'
                    s = "".join(parts[:-1]) + "." + parts[-1]
                try:
                    return float(s)
                except ValueError:
                    return None

            df["Amount"] = df["Amount"].apply(clean_num)
            df["EMI"]    = df["EMI"].apply(clean_num)

            # Drop header-repeat rows or blank rows
            df = df.dropna(subset=["Amount", "EMI"])
            df = df[df["Amount"] > 0]
            df = df.reset_index(drop=True)

            return df, None
        except Exception as e:
            return None, str(e)

    # ── Upload or use saved file ─────────────────────────────────────────────
    uploaded = st.file_uploader("Update loans file (optional)", type=["xlsx","xls"])
    if uploaded:
        with open(str(LOANS_FILE), "wb") as f:
            f.write(uploaded.read())
        st.success("Loans file updated.")

    if not LOANS_FILE.exists():
        st.warning("No loans file found. Please upload your loans.xlsx above.")
        st.stop()

    df_loans, err = load_loans(LOANS_FILE)
    if err or df_loans is None:
        st.error(f"Could not load loans file: {err}")
        st.stop()

    # ── Derived columns ──────────────────────────────────────────────────────
    df_loans["Annual EMI"]     = df_loans["EMI"] * 12
    df_loans["Est. Months"]    = (df_loans["Amount"] / df_loans["EMI"]).round(1)
    df_loans["% of Total Debt"]= (df_loans["Amount"] / df_loans["Amount"].sum() * 100).round(1)

    # Category from bank name
    def categorise(name):
        n = str(name).upper()
        if "CREDIT LINE" in n:  return "Credit Line"
        if "QUICK CASH"  in n:  return "Quick Cash"
        return "Term Loan"
    df_loans["Category"] = df_loans["Bank"].apply(categorise)

    total_debt   = df_loans["Amount"].sum()
    total_emi    = df_loans["EMI"].sum()
    annual_emi   = total_emi * 12
    num_loans    = len(df_loans)
    avg_months   = (df_loans["Amount"] / df_loans["EMI"]).mean()

    # ── HERO METRICS ─────────────────────────────────────────────────────────
    def loan_metric(label, value_str, sub="", color="#E8EEFF"):
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#151929,#1C2138);
                    border:1px solid #252A45;border-radius:14px;
                    padding:14px 16px;box-shadow:0 4px 16px rgba(0,0,0,0.35);">
            <div style="font-size:0.72rem;color:#6B748F;text-transform:uppercase;
                        letter-spacing:0.06em;margin-bottom:6px">{label}</div>
            <div style="font-size:1.25rem;font-weight:700;color:{color}">{value_str}</div>
            <div style="font-size:0.78rem;color:#9BA3C0;margin-top:2px">{sub}</div>
        </div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: loan_metric("Total Outstanding", f"S${total_debt:,.0f}", f"{num_loans} active loans", "#EF4444")
    with c2: loan_metric("Monthly EMI", f"S${total_emi:,.2f}", "total commitment/month", "#F59E0B")
    with c3: loan_metric("Annual Burden", f"S${annual_emi:,.0f}", "total EMI per year", "#F59E0B")
    with c4: loan_metric("Avg. Payoff", f"{avg_months:.0f} months", f"~{avg_months/12:.1f} years at current EMI", "#60A5FA")

    st.markdown("---")

    # ── ROW 2: Category summary ───────────────────────────────────────────────
    st.markdown("### By Category")
    cat_df = df_loans.groupby("Category").agg(
        Loans    = ("Bank",   "count"),
        Amount   = ("Amount", "sum"),
        EMI      = ("EMI",    "sum"),
    ).reset_index()

    colors_map = {"Credit Line": "#60A5FA", "Quick Cash": "#F59E0B", "Term Loan": "#A78BFA"}
    cols = st.columns(len(cat_df))
    for i, row in cat_df.iterrows():
        clr = colors_map.get(row["Category"], "#E8EEFF")
        with cols[i]:
            loan_metric(
                row["Category"],
                f"S${row['Amount']:,.0f}",
                f"{row['Loans']} loans · S${row['EMI']:,.2f}/mo",
                clr
            )

    st.markdown("---")

    # ── ROW 3: Charts ────────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Loan Composition")
        fig_pie = go.Figure(go.Pie(
            labels   = df_loans["Bank"],
            values   = df_loans["Amount"],
            hole     = 0.55,
            textinfo = "percent",
            hovertemplate = "<b>%{label}</b><br>S$%{value:,.0f}<br>%{percent}<extra></extra>",
            marker   = dict(colors=px.colors.qualitative.Bold),
        ))
        fig_pie.add_annotation(
            text=f"S${total_debt/1000:.0f}K<br><span style='font-size:11px'>Total</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#E8EEFF"),
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#9BA3C0", showlegend=True,
            legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
            margin=dict(t=10, b=10, l=10, r=10), height=320,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.markdown("#### Monthly EMI per Loan")
        df_sorted = df_loans.sort_values("EMI", ascending=True)
        fig_bar = go.Figure(go.Bar(
            x            = df_sorted["EMI"],
            y            = df_sorted["Bank"],
            orientation  = "h",
            marker_color = [colors_map.get(c, "#60A5FA") for c in df_sorted["Category"]],
            text         = [f"S${v:,.0f}" for v in df_sorted["EMI"]],
            textposition = "outside",
            hovertemplate= "<b>%{y}</b><br>EMI: S$%{x:,.2f}<extra></extra>",
        ))
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#9BA3C0", xaxis=dict(showgrid=False, color="#6B748F"),
            yaxis=dict(showgrid=False, color="#9BA3C0"),
            margin=dict(t=10, b=10, l=10, r=60), height=320,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── ROW 4: Payoff timeline ────────────────────────────────────────────────
    st.markdown("#### Estimated Payoff Timeline")
    df_tl = df_loans[["Bank","Amount","EMI","Est. Months","Category"]].copy()
    df_tl = df_tl.sort_values("Est. Months", ascending=False)

    fig_tl = go.Figure()
    for _, row in df_tl.iterrows():
        clr = colors_map.get(row["Category"], "#60A5FA")
        fig_tl.add_trace(go.Bar(
            name         = row["Bank"],
            x            = [row["Est. Months"]],
            y            = [row["Bank"]],
            orientation  = "h",
            marker_color = clr,
            text         = [f"{row['Est. Months']:.0f} mo  (S${row['Amount']:,.0f})"],
            textposition = "outside",
            hovertemplate= f"<b>{row['Bank']}</b><br>~{row['Est. Months']:.0f} months<br>Outstanding: S${row['Amount']:,.0f}<extra></extra>",
        ))
    fig_tl.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#9BA3C0", showlegend=False,
        xaxis=dict(title="Estimated Months Remaining", color="#6B748F", showgrid=False),
        yaxis=dict(showgrid=False, color="#9BA3C0"),
        margin=dict(t=10, b=40, l=10, r=120), height=320,
    )
    st.plotly_chart(fig_tl, use_container_width=True)

    # ── ROW 5: Full table ─────────────────────────────────────────────────────
    st.markdown("#### Loan Details")
    display_df = df_loans[["Bank","Category","Amount","EMI","Annual EMI","Est. Months","% of Total Debt"]].copy()
    display_df = display_df.rename(columns={"Est. Months":"Est. Months Left"})

    # Format for display
    fmt_df = display_df.copy()
    fmt_df["Amount"]        = fmt_df["Amount"].apply(lambda v: f"S${v:,.2f}")
    fmt_df["EMI"]           = fmt_df["EMI"].apply(lambda v: f"S${v:,.2f}")
    fmt_df["Annual EMI"]    = fmt_df["Annual EMI"].apply(lambda v: f"S${v:,.2f}")
    fmt_df["% of Total Debt"] = fmt_df["% of Total Debt"].apply(lambda v: f"{v:.1f}%")

    # Totals row
    totals = {
        "Bank": "TOTAL", "Category": "",
        "Amount": f"S${total_debt:,.2f}",
        "EMI": f"S${total_emi:,.2f}",
        "Annual EMI": f"S${annual_emi:,.2f}",
        "Est. Months Left": "—",
        "% of Total Debt": "100%"
    }
    fmt_df = pd.concat([fmt_df, pd.DataFrame([totals])], ignore_index=True)

    st.dataframe(fmt_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.caption(f"Data last loaded from loans.xlsx · {num_loans} loans · Total EMI S${total_emi:,.2f}/month")

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
if nav == "⚙️ Settings":
    st.title("⚙️ Settings")

    st.markdown("### Angel One (India) — SmartAPI Credentials")

    # Show whether credentials are coming from env vars or settings file
    env_keys = ["ANGEL_API_KEY", "ANGEL_CLIENT_ID", "ANGEL_PASSWORD", "ANGEL_TOTP_SECRET"]
    using_env = all(_os.environ.get(k, "").strip() for k in env_keys)
    if using_env:
        st.success("✅ Credentials loaded from **environment variables** (Railway deployment). "
                   "To change them, update the Variables in your Railway project dashboard.")
    else:
        st.info("Get your API key from [Angel One SmartAPI](https://smartapi.angelbroking.com/). "
                "Enable TOTP in your Angel One app to get the TOTP secret.")

    with st.form("angel_settings"):
        col1, col2 = st.columns(2)
        with col1:
            angel_key    = st.text_input("API Key",       value=settings.get("angel_api_key", ""),    type="password")
            angel_id     = st.text_input("Client ID",     value=settings.get("angel_client_id", ""))
        with col2:
            angel_pass   = st.text_input("Password/PIN",  value=settings.get("angel_password", ""),   type="password")
            angel_totp   = st.text_input("TOTP Secret",   value=settings.get("angel_totp_secret", ""),type="password")

        if st.form_submit_button("💾 Save Angel One Settings", use_container_width=True):
            settings.update({
                "angel_api_key":     angel_key,
                "angel_client_id":   angel_id,
                "angel_password":    angel_pass,
                "angel_totp_secret": angel_totp,
            })
            save_json(SETTINGS_FILE, settings)
            st.session_state.settings = settings
            st.success("✅ Angel One credentials saved!")

    st.markdown("---")
    st.markdown("### Display Preferences")
    with st.form("display_settings"):
        base_currency = st.selectbox(
            "Base currency for totals",
            ["INR (₹)", "USD ($)", "GBP (£)"],
            index=["INR (₹)", "USD ($)", "GBP (£)"].index(settings.get("base_currency", "INR (₹)")),
        )
        if st.form_submit_button("💾 Save Display Settings", use_container_width=True):
            settings["base_currency"] = base_currency
            save_json(SETTINGS_FILE, settings)
            st.session_state.settings = settings
            st.success("✅ Display settings saved!")

    st.markdown("---")
    st.markdown("### ℹ️ About Vested & JP Morgan")
    st.warning(
        "**Vested Finance** and **JP Morgan Workplace Solutions** do not offer public APIs. "
        "You can manage your US and UK holdings manually in their respective tabs, "
        "or import them using a CSV file. Live prices will be fetched automatically via Yahoo Finance."
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: INDIA (Angel One)
# ══════════════════════════════════════════════════════════════════════════════
elif nav == "🇮🇳 India (Angel One)":
    st.title("🇮🇳 India Portfolio — Angel One")

    # Check credentials
    has_creds = all([
        settings.get("angel_api_key"),
        settings.get("angel_client_id"),
        settings.get("angel_password"),
        settings.get("angel_totp_secret"),
    ])

    if not has_creds:
        st.warning("⚠️ Angel One credentials not configured. Go to **⚙️ Settings** to add them.")
        st.stop()

    col_btn, col_status = st.columns([2, 5])
    with col_btn:
        fetch_clicked = st.button("🔌 Connect & Fetch Holdings", use_container_width=True)

    if fetch_clicked:
        with st.spinner("Connecting to Angel One..."):
            try:
                from utils.angel_api import AngelOneClient
                client = AngelOneClient(
                    api_key=settings["angel_api_key"],
                    client_id=settings["angel_client_id"],
                    password=settings["angel_password"],
                    totp_secret=settings["angel_totp_secret"],
                )
                df, error = client.get_holdings()
                if error:
                    st.session_state.angel_error = error
                    st.session_state.angel_holdings = None
                else:
                    st.session_state.angel_holdings = df
                    st.session_state.angel_error = None
                    st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")
            except Exception as e:
                st.session_state.angel_error = str(e)
                st.session_state.angel_holdings = None

    if st.session_state.angel_error:
        st.error(f"❌ {st.session_state.angel_error}")

    df = st.session_state.angel_holdings

    if df is not None and not df.empty:
        st.markdown('<span class="success-badge">✓ Connected</span>', unsafe_allow_html=True)

        # ── Debug: show raw columns so we can verify field names ─────────────
        with st.expander("🔍 Raw API data (for debugging)", expanded=False):
            st.write("**Columns returned by Angel One:**", list(df.columns))
            st.dataframe(df.head(3), use_container_width=True)

        st.markdown("---")

        # ── Derive missing columns from what Angel One does return ────────────
        for col in ["quantity", "averageprice", "ltp", "profitandloss", "pnlpercentage"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Angel One v2 doesn't return investedvalue / totvalue — compute them
        if "investedvalue" not in df.columns:
            df["investedvalue"] = df["quantity"] * df["averageprice"]
        if "totvalue" not in df.columns:
            df["totvalue"] = df["quantity"] * df["ltp"]
        # Recompute P&L from derived values for accuracy
        df["profitandloss"] = df["totvalue"] - df["investedvalue"]
        df["pnlpercentage"] = (df["profitandloss"] / df["investedvalue"].replace(0, pd.NA)) * 100

        # Compute totals
        total_invested = df["investedvalue"].sum()
        total_current  = df["totvalue"].sum()
        total_pnl      = total_current - total_invested
        pnl_pct        = (total_pnl / total_invested * 100) if total_invested else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Invested (INR)",       fmt_inr(total_invested))
        c2.metric("Current Value (INR)",  fmt_inr(total_current))
        delta_color = "normal" if total_pnl >= 0 else "inverse"
        c3.metric("Total P&L",            fmt_inr(total_pnl),    f"{pnl_pct:+.2f}%", delta_color=delta_color)
        c4.metric("Holdings",             len(df))

        st.markdown("---")

        # ── Holdings table ────────────────────────────────────────────────────
        st.markdown("### Holdings")
        show_df = pd.DataFrame({
            "Symbol":        df["tradingsymbol"],
            "Qty":           df["quantity"],
            "Avg Price":     df["averageprice"].apply(lambda x: f"₹{x:,.2f}"),
            "LTP":           df["ltp"].apply(lambda x: f"₹{x:,.2f}"),
            "Invested":      df["investedvalue"].apply(fmt_inr),
            "Current Value": df["totvalue"].apply(fmt_inr),
            "P&L":           df["profitandloss"].apply(fmt_inr),
            "P&L %":         df["pnlpercentage"].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "—"),
        })

        st.dataframe(show_df, use_container_width=True, hide_index=True)

        # Also update session state with enriched df
        st.session_state.angel_holdings = df

        # ── Chart: P&L by stock ───────────────────────────────────────────────
        if "profitandloss" in df.columns and "tradingsymbol" in df.columns:
            st.markdown("### P&L by Stock")
            chart_df = df[["tradingsymbol", "profitandloss"]].copy()
            chart_df.columns = ["Symbol", "PnL"]
            chart_df["PnL"] = pd.to_numeric(chart_df["PnL"], errors="coerce")
            chart_df = chart_df.dropna().sort_values("PnL")
            chart_df["Color"] = chart_df["PnL"].apply(lambda x: "#00C875" if x >= 0 else "#E2445C")

            fig = go.Figure(go.Bar(
                x=chart_df["PnL"],
                y=chart_df["Symbol"],
                orientation="h",
                marker_color=chart_df["Color"],
                text=chart_df["PnL"].apply(lambda x: fmt_inr(x)),
                textposition="outside",
            ))
            fig.update_layout(
                paper_bgcolor="#1E2130", plot_bgcolor="#1E2130",
                font=dict(color="#C0C4D0"),
                margin=dict(l=10, r=20, t=20, b=10),
                height=max(300, len(chart_df) * 30),
                xaxis=dict(showgrid=False, zeroline=True, zerolinecolor="#3E4460"),
                yaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        if not fetch_clicked:
            st.info("Click **Connect & Fetch Holdings** to load your Angel One portfolio.")

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: US (Vested)
# ══════════════════════════════════════════════════════════════════════════════
elif nav == "🇺🇸 US (Vested)":
    st.title("🇺🇸 US Portfolio — Vested Finance")

    import io as _io

    # ── File uploader (optional — saved file loads automatically) ─────────────
    with st.expander("📂 Update Holdings File", expanded=not VESTED_HOLDINGS_FILE.exists()):
        col_up, col_hint = st.columns([2, 3])
        with col_up:
            vhf = st.file_uploader(
                "Vested_Holdings.xlsx",
                type=["xlsx"],
                key="us_holdings_upload",
                help="Download from Vested app → Portfolio → Export",
            )
        with col_hint:
            if VESTED_HOLDINGS_FILE.exists():
                st.success(f"Using saved holdings file — upload a new one to replace it.")
            else:
                st.info("Download from the Vested app:\n**Portfolio → menu → Export Holdings**")

        if vhf:
            raw = vhf.read()
            with open(str(VESTED_HOLDINGS_FILE), "wb") as _f:
                _f.write(raw)
            st.success("Holdings file saved — will load automatically from now on.")
            st.rerun()

    with st.expander("📂 Update Transactions File", expanded=not VESTED_TRANSACTIONS_FILE.exists()):
        col_t, col_th = st.columns([2, 3])
        with col_t:
            vtf = st.file_uploader(
                "Vested_Transactions.xlsx",
                type=["xlsx"],
                key="us_txn_upload",
                help="Download from Vested app → Transactions → Export",
            )
        with col_th:
            if VESTED_TRANSACTIONS_FILE.exists():
                st.success("Using saved transactions file — upload a new one to replace it.")
            else:
                st.info("Used to calculate **Total Deposited** on the Dashboard.")
        if vtf:
            raw = vtf.read()
            with open(str(VESTED_TRANSACTIONS_FILE), "wb") as _f:
                _f.write(raw)
            st.success("Transactions file saved.")
            st.rerun()

    @st.cache_data(show_spinner=False)
    def parse_vested_holdings(file_path_str):
        xl = pd.ExcelFile(file_path_str)
        summary = {}
        holdings = pd.DataFrame()

        if "Summary" in xl.sheet_names:
            df = xl.parse("Summary")
            df.columns = [c.strip() for c in df.columns]
            if not df.empty:
                row = df.iloc[0]
                summary = {
                    "current_value":  float(str(row.get("Current Equity Value (USD)",  0)).replace(",","").replace("%","") or 0),
                    "total_invested": float(str(row.get("Total Amount Invested (USD)", 0)).replace(",","").replace("%","") or 0),
                    "returns_usd":    float(str(row.get("Investment Returns (USD)",    0)).replace(",","").replace("%","") or 0),
                    "returns_pct":    str(row.get("Investment Returns (%)", "0%")),
                }

        if "Holdings" in xl.sheet_names:
            holdings = xl.parse("Holdings")
            holdings.columns = [c.strip() for c in holdings.columns]
            numeric_cols = [
                "Total Shares Held", "Current Price (USD)", "Current Value (USD)",
                "Average Cost (USD)", "Total Amount Invested (USD)",
                "Investment Returns (USD)", "Investment Returns (%)",
                "Daily Change (USD)", "Daily Change (%)",
            ]
            for col in numeric_cols:
                if col in holdings.columns:
                    holdings[col] = pd.to_numeric(holdings[col], errors="coerce")

        return summary, holdings

    if not VESTED_HOLDINGS_FILE.exists():
        st.info("No holdings file found. Expand **Update Holdings File** above to upload one.")
        st.stop()

    summary, holdings = parse_vested_holdings(str(VESTED_HOLDINGS_FILE))

    # ── Fetch live FX rates ────────────────────────────────────────────────────
    with st.spinner("Fetching live prices…"):
        try:
            from utils.price_fetcher import get_fx_rates, get_prices_bulk
            fx = get_fx_rates()
            st.session_state.fx_rates = fx
        except Exception:
            fx = {"USD": 84.0}
    usd_inr = fx.get("USD", 84.0)

    # ── Fetch live prices for each ticker ──────────────────────────────────────
    if not holdings.empty and "Ticker" in holdings.columns:
        tickers = holdings["Ticker"].dropna().tolist()
        with st.spinner("Fetching live US stock prices…"):
            try:
                live_prices = get_prices_bulk(tickers)
            except Exception:
                live_prices = {}

        # Overwrite price columns with live data
        def live_price(ticker):
            return live_prices.get(ticker, {}).get("price") or None

        holdings["Live Price (USD)"]  = holdings["Ticker"].map(live_price)
        holdings["Live Value (USD)"]  = holdings["Total Shares Held"] * holdings["Live Price (USD)"]
        holdings["Live Returns (USD)"] = holdings["Live Value (USD)"] - holdings["Total Amount Invested (USD)"]
        holdings["Live Returns (%)"]  = (holdings["Live Returns (USD)"] / holdings["Total Amount Invested (USD)"] * 100).round(2)
        holdings["Daily Change (%)"]  = holdings["Ticker"].map(
            lambda t: live_prices.get(t, {}).get("daily_change_pct") or None)
    else:
        live_prices = {}

    # ── Recalculate summary from live prices ───────────────────────────────────
    live_total_value    = holdings["Live Value (USD)"].sum()    if "Live Value (USD)"   in holdings.columns else 0
    live_total_invested = holdings["Total Amount Invested (USD)"].sum() if "Total Amount Invested (USD)" in holdings.columns else 0
    live_total_returns  = live_total_value - live_total_invested
    live_returns_pct    = (live_total_returns / live_total_invested * 100) if live_total_invested else 0

    # Update session state with live values for Dashboard
    st.session_state.us_vested_summary = {
        "current_value":  live_total_value,
        "total_invested": live_total_invested,
        "returns_usd":    live_total_returns,
        "returns_pct":    f"{live_returns_pct:+.2f}%",
    }

    # ── Summary cards ──────────────────────────────────────────────────────────
    st.markdown("---")
    vc1, vc2, vc3, vc4 = st.columns(4)
    vc1.metric("💵 Live Value",      f"${live_total_value:,.2f}",
               f"≈ {fmt_inr(live_total_value * usd_inr)}")
    vc2.metric("📥 Cost Basis",      f"${live_total_invested:,.2f}",
               f"≈ {fmt_inr(live_total_invested * usd_inr)}")
    vc3.metric("📈 Returns (USD)",   f"${live_total_returns:+,.2f}",
               f"{live_returns_pct:+.2f}%",
               delta_color="normal" if live_total_returns >= 0 else "inverse")
    vc4.metric("🔢 Holdings",        str(len(holdings)))

    st.markdown("---")

    if holdings.empty:
        st.warning("No holdings data found in the file.")
        st.stop()

    # ── Holdings table with live prices ───────────────────────────────────────
    st.markdown("### Holdings (Live Prices)")
    disp = pd.DataFrame()
    disp["Company"]        = holdings.get("Name", holdings.get("Ticker", "—"))
    disp["Ticker"]         = holdings["Ticker"]
    disp["Shares"]         = holdings["Total Shares Held"].map(lambda x: f"{x:.4f}" if pd.notna(x) else "—")
    disp["Avg Cost"]       = holdings["Average Cost (USD)"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "—")
    disp["Live Price"]     = holdings["Live Price (USD)"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "—")
    disp["Invested"]       = holdings["Total Amount Invested (USD)"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "—")
    disp["Live Value"]     = holdings["Live Value (USD)"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "—")
    disp["Value (INR)"]    = holdings["Live Value (USD)"].map(lambda x: fmt_inr(x * usd_inr) if pd.notna(x) else "—")
    disp["Returns"]        = holdings["Live Returns (USD)"].map(
        lambda x: (f"+${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}") if pd.notna(x) else "—")
    disp["Returns %"]      = holdings["Live Returns (%)"].map(
        lambda x: f"{x:+.2f}%" if pd.notna(x) else "—")
    disp["Day Change %"]   = holdings["Daily Change (%)"].map(
        lambda x: f"{x:+.2f}%" if pd.notna(x) else "—")

    st.dataframe(disp, use_container_width=True, hide_index=True)

    # ── P&L bar chart (live) ───────────────────────────────────────────────────
    st.markdown("### Live Returns by Stock")
    if "Live Returns (USD)" in holdings.columns:
        chart = holdings[["Ticker", "Live Returns (USD)", "Name"]].dropna().sort_values("Live Returns (USD)")
        fig = px.bar(
            chart, x="Live Returns (USD)", y="Ticker", orientation="h",
            color="Live Returns (USD)",
            color_continuous_scale=["#EF4444", "#F97316", "#22C55E"],
            labels={"Live Returns (USD)": "Returns (USD)", "Ticker": ""},
            hover_data=["Name"],
        )
        fig.add_vline(x=0, line_color="#6b7280", line_dash="dash")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#C0C4D0"),
            coloraxis_showscale=False,
            margin=dict(l=0, r=20, t=10, b=0),
            height=max(280, len(chart) * 42),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Store enriched holdings in session state for Dashboard ─────────────────
    st.session_state.us_vested_summary  = summary
    st.session_state.us_vested_holdings = holdings


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: UK (JP Morgan)
# ══════════════════════════════════════════════════════════════════════════════
elif nav == "🇬🇧 UK (JP Morgan)":
    st.title("🇬🇧 UK Portfolio — JP Morgan Workplace Solutions")

    uk_holdings = load_json(UK_HOLDINGS_FILE, [])

    st.markdown("### Add / Manage UK Holdings")
    st.info("JP Morgan WPS has no public API. Add holdings manually or import a CSV. "
            "Live prices are fetched from Yahoo Finance automatically.\n\n"
            "Use **.L suffix** for LSE stocks, e.g. `LLOY.L`, `BP.L`, `SHEL.L`")

    # ── CSV import ─────────────────────────────────────────────────────────────
    with st.expander("📂 Import from CSV", expanded=False):
        st.markdown("CSV format: `Company, Ticker, Qty, Avg (GBP)` — multiple lots of the "
                    "same ticker are combined with a weighted average price.")
        uk_csv = st.file_uploader("Upload CSV", type=["csv"], key="uk_csv_upload")
        if uk_csv:
            import io as _io
            try:
                raw = pd.read_csv(_io.BytesIO(uk_csv.read()), encoding="utf-8-sig")
                raw = raw.dropna(axis=1, how="all")
                raw = raw[raw.columns[:4]]
                raw.columns = ["company", "ticker", "qty", "avg_gbp"]
                raw["qty"]     = pd.to_numeric(raw["qty"], errors="coerce")
                raw["avg_gbp"] = pd.to_numeric(
                    raw["avg_gbp"].astype(str).str.replace("£", "").str.strip(), errors="coerce")
                raw = raw.dropna(subset=["ticker", "qty", "avg_gbp"])
                imported = []
                for ticker_val, grp in raw.groupby("ticker"):
                    tq  = float(grp["qty"].sum())
                    ti  = float((grp["qty"] * grp["avg_gbp"]).sum())
                    imported.append({
                        "ticker":        str(ticker_val),
                        "name":          str(grp["company"].iloc[0]),
                        "qty":           round(tq, 4),
                        "avg_price_gbp": round(ti / tq, 4),
                        "sector":        "",
                    })
                # Merge with existing (replace matching tickers)
                existing = {h["ticker"]: h for h in uk_holdings}
                for h in imported:
                    existing[h["ticker"]] = h
                uk_holdings = list(existing.values())
                save_json(UK_HOLDINGS_FILE, uk_holdings)
                st.success(f"✅ Imported {len(imported)} holding(s) from CSV")
                st.rerun()
            except Exception as e:
                st.error(f"CSV parse error: {e}")

    # ── Add holding form ───────────────────────────────────────────────────────
    with st.expander("➕ Add a holding manually", expanded=len(uk_holdings) == 0):
        with st.form("add_uk"):
            fc1, fc2, fc3 = st.columns(3)
            uk_ticker = fc1.text_input("Ticker (e.g. LLOY.L)")
            uk_name   = fc2.text_input("Company Name")
            uk_qty    = fc1.number_input("Quantity", min_value=0.0, step=0.01)
            uk_price  = fc2.number_input("Avg Buy Price (GBP)", min_value=0.0, step=0.01)
            uk_sector = fc3.text_input("Sector (optional)")
            if st.form_submit_button("Add Holding"):
                if uk_ticker and uk_qty > 0:
                    uk_holdings.append({
                        "ticker": uk_ticker.strip().upper(),
                        "name": uk_name or uk_ticker.strip().upper(),
                        "qty": uk_qty,
                        "avg_price_gbp": uk_price,
                        "sector": uk_sector,
                    })
                    save_json(UK_HOLDINGS_FILE, uk_holdings)
                    st.success(f"Added {uk_ticker.upper()}")
                    st.rerun()

    if not uk_holdings:
        st.info("No UK holdings yet. Add your first holding above.")
        st.stop()

    # ── Fetch live prices ──────────────────────────────────────────────────────
    tickers = [h["ticker"] for h in uk_holdings]
    with st.spinner("Fetching live prices…"):
        try:
            from utils.price_fetcher import get_prices_bulk, get_fx_rates
            prices = get_prices_bulk(tickers)
            fx     = get_fx_rates()
            st.session_state.fx_rates = fx
        except Exception:
            prices = {}
            fx     = {"GBP": 107.0, "USD": 84.0, "INR": 1.0}

    gbp_inr = fx.get("GBP", 107.0)

    rows = []
    for h in uk_holdings:
        t   = h["ticker"]
        pi  = prices.get(t, {})
        ltp = pi.get("price") or 0.0
        # LSE prices sometimes quoted in pence — convert if > 500
        if ltp > 500:
            ltp = ltp / 100
        qty     = float(h.get("qty", 0))
        avg     = float(h.get("avg_price_gbp", 0))
        invested = qty * avg
        current  = qty * ltp
        pnl      = current - invested
        pnl_pct  = (pnl / invested * 100) if invested else 0
        rows.append({
            "Ticker":       t,
            "Company":      h.get("name", t),
            "Qty":          qty,
            "Avg (GBP)":    f"£{avg:,.2f}",
            "LTP (GBP)":    f"£{ltp:,.2f}" if ltp else "—",
            "Invested":     f"£{invested:,.2f}",
            "Value (GBP)":  f"£{current:,.2f}",
            "Value (INR)":  fmt_inr(current * gbp_inr),
            "P&L (GBP)":    f"£{pnl:+,.2f}",
            "P&L %":        f"{pnl_pct:+.2f}%",
            "_invested":    invested,
            "_current":     current,
            "_pnl":         pnl,
        })

    df_uk = pd.DataFrame(rows)
    total_inv_gbp = df_uk["_invested"].sum()
    total_cur_gbp = df_uk["_current"].sum()
    total_pnl_gbp = df_uk["_pnl"].sum()
    pnl_pct_total = (total_pnl_gbp / total_inv_gbp * 100) if total_inv_gbp else 0

    kc1, kc2, kc3, kc4 = st.columns(4)
    kc1.metric("Invested (GBP)",      f"£{total_inv_gbp:,.2f}", fmt_inr(total_inv_gbp * gbp_inr))
    kc2.metric("Current Value (GBP)", f"£{total_cur_gbp:,.2f}", fmt_inr(total_cur_gbp * gbp_inr))
    kc3.metric("P&L (GBP)",           f"£{total_pnl_gbp:+,.2f}", f"{pnl_pct_total:+.2f}%",
               delta_color="normal" if total_pnl_gbp >= 0 else "inverse")
    kc4.metric("Holdings",            str(len(df_uk)))

    st.markdown("---")
    st.markdown("### Holdings")
    show_cols = ["Company","Ticker","Qty","Avg (GBP)","LTP (GBP)","Invested","Value (GBP)","Value (INR)","P&L (GBP)","P&L %"]
    st.dataframe(df_uk[show_cols], use_container_width=True, hide_index=True)

    # ── Delete holding ─────────────────────────────────────────────────────────
    with st.expander("🗑️ Remove a holding"):
        del_ticker = st.selectbox("Select ticker to remove", [h["ticker"] for h in uk_holdings])
        if st.button("Remove", type="secondary"):
            uk_holdings = [h for h in uk_holdings if h["ticker"] != del_ticker]
            save_json(UK_HOLDINGS_FILE, uk_holdings)
            st.success(f"Removed {del_ticker}")
            st.rerun()

    # ── P&L chart ──────────────────────────────────────────────────────────────
    st.markdown("### P&L by Stock")
    fig_uk = px.bar(
        df_uk.sort_values("_pnl"), x="_pnl", y="Ticker", orientation="h",
        color="_pnl", color_continuous_scale=["#E2445C","#F97316","#22C55E"],
        labels={"_pnl": "P&L (GBP)", "Ticker": ""},
    )
    fig_uk.add_vline(x=0, line_color="#6b7280", line_dash="dash")
    fig_uk.update_layout(
        paper_bgcolor="#1E2130", plot_bgcolor="#1E2130",
        font=dict(color="#C0C4D0"), coloraxis_showscale=False,
        margin=dict(l=0, r=20, t=10, b=0),
        height=max(280, len(df_uk) * 38),
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
    )
    st.plotly_chart(fig_uk, use_container_width=True)

    # Store for dashboard
    st.session_state.uk_total_invested_gbp = total_inv_gbp
    st.session_state.uk_total_current_gbp  = total_cur_gbp
    st.session_state.uk_gbp_inr            = gbp_inr


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif nav == "🏠 Dashboard":
    st.title("🏠 Portfolio Dashboard")


    # ── Custom colored metric card ─────────────────────────────────────────────
    def dash_metric(label, value_str, delta_str="", positive=None):
        """Render a metric card: green if positive=True, red if False, white if None."""
        val_color  = "#22C55E" if positive is True else "#EF4444" if positive is False else "#E8EEFF"
        delt_color = "#22C55E" if positive is True else "#EF4444" if positive is False else "#9BA3C0"
        delta_part = (
            '<p style="font-size:0.78rem;color:' + delt_color + ';margin:2px 0 0 0">' + delta_str + '</p>'
            if delta_str else ""
        )
        html = (
            '<div style="background:linear-gradient(135deg,#151929,#1C2138);'
            'border:1px solid #252A45;border-radius:14px;'
            'padding:14px 16px;box-shadow:0 4px 16px rgba(0,0,0,0.35);">'
            '<p style="font-size:0.72rem;color:#6B748F;text-transform:uppercase;'
            'letter-spacing:0.06em;margin:0 0 6px 0">' + label + '</p>'
            '<p style="font-size:1.25rem;font-weight:700;color:' + val_color + ';margin:0">'
            + value_str + '</p>'
            + delta_part +
            '</div>'
        )
        st.markdown(html, unsafe_allow_html=True)

    # ── Fetch FX + live prices ─────────────────────────────────────────────────
    with st.spinner("Fetching live rates…"):
        try:
            from utils.price_fetcher import get_fx_rates, get_prices_bulk
            fx = get_fx_rates()
            st.session_state.fx_rates = fx
        except Exception:
            fx = {"USD": 84.0, "GBP": 107.0, "INR": 1.0,
                  "USD_SGD": 1.35, "GBP_SGD": 1.71, "INR_SGD": 0.016}

    usd_sgd = fx.get("USD_SGD", 1.35)
    gbp_sgd = fx.get("GBP_SGD", 1.71)
    inr_sgd = fx.get("INR_SGD", 0.016)

    def fmt_sgd_plain(v):
        try: return f"S${float(v):,.2f}"
        except: return "—"
    def fmt_sgd_signed(v):
        try:
            v = float(v)
            return f"+S${v:,.2f}" if v >= 0 else f"-S${abs(v):,.2f}"
        except: return "—"

    # ════════════════════════════════════════════════════════════════
    #  INDIA — auto-fetch if credentials set, session state not loaded
    # ════════════════════════════════════════════════════════════════
    india_invested_sgd  = 0.0
    india_current_sgd   = 0.0
    india_daily_sgd     = 0.0
    india_daily_pct     = 0.0
    india_current_inr   = 0.0
    india_daily_inr_val = 0.0

    india_funds_data   = load_json(str(INDIA_FUNDS_FILE), {})
    india_invested_inr = float(india_funds_data.get("net_added", 0))
    india_invested_sgd = india_invested_inr * inr_sgd

    df_india = st.session_state.get("angel_holdings")

    if df_india is None:
        has_creds = all([settings.get("angel_api_key"), settings.get("angel_client_id"),
                         settings.get("angel_password"), settings.get("angel_totp_secret")])
        if has_creds:
            with st.spinner("Fetching India holdings…"):
                try:
                    from utils.angel_api import AngelOneClient
                    _client = AngelOneClient(
                        api_key=settings["angel_api_key"],
                        client_id=settings["angel_client_id"],
                        password=settings["angel_password"],
                        totp_secret=settings["angel_totp_secret"],
                    )
                    _df, _err = _client.get_holdings()
                    if _err:
                        st.warning(f"India: {_err}")
                    else:
                        for col in ["quantity", "averageprice", "ltp", "close"]:
                            if col in _df.columns:
                                _df[col] = pd.to_numeric(_df[col], errors="coerce").fillna(0)
                        if "investedvalue" not in _df.columns:
                            _df["investedvalue"] = _df["quantity"] * _df["averageprice"]
                        if "totvalue" not in _df.columns:
                            _df["totvalue"] = _df["quantity"] * _df["ltp"]
                        st.session_state.angel_holdings = _df
                        df_india = _df
                        st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")
                except Exception as e:
                    st.warning(f"India auto-connect failed: {e}")

    if df_india is not None and not df_india.empty:
        if "totvalue" in df_india.columns:
            india_current_inr = float(df_india["totvalue"].sum())
            india_current_sgd = india_current_inr * inr_sgd
        if all(c in df_india.columns for c in ["ltp", "close", "quantity"]):
            india_daily_inr_val = float(
                ((df_india["ltp"] - df_india["close"]) * df_india["quantity"]).sum()
            )
            india_daily_sgd = india_daily_inr_val * inr_sgd
            base = india_current_inr - india_daily_inr_val
            india_daily_pct = (india_daily_inr_val / base * 100) if base else 0

    # ════════════════════════════════════════════════════════════════
    #  US — saved files + live prices
    # ════════════════════════════════════════════════════════════════
    us_invested_sgd = 0.0
    us_current_sgd  = 0.0
    us_daily_sgd    = 0.0
    us_daily_pct    = 0.0
    us_invested_usd = 0.0
    us_current_usd  = 0.0
    us_daily_usd    = 0.0

    if VESTED_TRANSACTIONS_FILE.exists():
        try:
            _xl  = pd.ExcelFile(str(VESTED_TRANSACTIONS_FILE))
            _trf = _xl.parse("Transfers")
            _trf.columns = [c.strip() for c in _trf.columns]
            _amt = next((c for c in _trf.columns if "Cash Amount" in c), None)
            if _amt:
                us_invested_usd = float(pd.to_numeric(_trf[_amt], errors="coerce").fillna(0).sum())
                us_invested_sgd = us_invested_usd * usd_sgd
        except Exception:
            pass

    if VESTED_HOLDINGS_FILE.exists():
        try:
            _xl  = pd.ExcelFile(str(VESTED_HOLDINGS_FILE))
            _hdf = _xl.parse("Holdings")
            _hdf.columns = [c.strip() for c in _hdf.columns]
            for col in ["Total Shares Held", "Total Amount Invested (USD)"]:
                if col in _hdf.columns:
                    _hdf[col] = pd.to_numeric(_hdf[col], errors="coerce").fillna(0)
            tickers_us = _hdf["Ticker"].dropna().tolist()
            lp_us = get_prices_bulk(tickers_us) if tickers_us else {}
            for _, row in _hdf.iterrows():
                t   = row.get("Ticker", "")
                qty = float(row.get("Total Shares Held", 0) or 0)
                pi  = lp_us.get(t, {})
                pr  = pi.get("price") or 0
                dcp = pi.get("daily_change_pct") or 0
                us_current_usd += qty * pr
                prev = pr / (1 + dcp / 100) if (1 + dcp / 100) != 0 else pr
                us_daily_usd   += qty * (pr - prev)
            us_current_sgd = us_current_usd * usd_sgd
            us_daily_sgd   = us_daily_usd   * usd_sgd
            base_us = us_current_usd - us_daily_usd
            us_daily_pct = (us_daily_usd / base_us * 100) if base_us else 0
        except Exception:
            pass

    # ════════════════════════════════════════════════════════════════
    #  UK — uk_holdings.json + live prices
    # ════════════════════════════════════════════════════════════════
    uk_invested_sgd = 0.0
    uk_current_sgd  = 0.0
    uk_daily_sgd    = 0.0
    uk_daily_pct    = 0.0

    uk_h = load_json(str(UK_HOLDINGS_FILE), [])
    if uk_h:
        tickers_uk = [h["ticker"] for h in uk_h]
        lp_uk = get_prices_bulk(tickers_uk)
        uk_invested_gbp = uk_current_gbp = uk_daily_gbp = 0.0
        for h in uk_h:
            t   = h["ticker"]
            qty = float(h.get("qty", 0))
            avg = float(h.get("avg_price_gbp", 0))
            pi  = lp_uk.get(t, {})
            ltp = pi.get("price") or 0
            if ltp > 500:
                ltp = ltp / 100
            dcp = pi.get("daily_change_pct") or 0
            prev = ltp / (1 + dcp / 100) if (1 + dcp / 100) != 0 else ltp
            uk_invested_gbp += qty * avg
            uk_current_gbp  += qty * ltp
            uk_daily_gbp    += qty * (ltp - prev)
        uk_invested_sgd = uk_invested_gbp * gbp_sgd
        uk_current_sgd  = uk_current_gbp  * gbp_sgd
        uk_daily_sgd    = uk_daily_gbp    * gbp_sgd
        base_uk = uk_current_gbp - uk_daily_gbp
        uk_daily_pct = (uk_daily_gbp / base_uk * 100) if base_uk else 0

    # ════════════════════════════════════════════════════════════════
    #  TOTALS
    # ════════════════════════════════════════════════════════════════
    total_invested  = india_invested_sgd + us_invested_sgd + uk_invested_sgd
    total_current   = india_current_sgd  + us_current_sgd  + uk_current_sgd
    total_pnl       = total_current - total_invested
    total_pnl_pct   = (total_pnl / total_invested * 100) if total_invested else 0
    total_daily     = india_daily_sgd + us_daily_sgd + uk_daily_sgd
    base_total      = total_current - total_daily
    total_daily_pct = (total_daily / base_total * 100) if base_total else 0

    # ════════════════════════════════════════════════════════════════
    #  TOP METRIC ROW
    # ════════════════════════════════════════════════════════════════
    t1, t2, t3, t4 = st.columns(4)
    with t1: dash_metric("Total Invested",  fmt_sgd_plain(total_invested))
    with t2: dash_metric("Current Value",   fmt_sgd_plain(total_current))
    with t3: dash_metric("Total P&L",       fmt_sgd_signed(total_pnl),
                          f"{total_pnl_pct:+.2f}%", positive=total_pnl >= 0)
    with t4: dash_metric("Today's Change", fmt_sgd_signed(total_daily),
                          f"{total_daily_pct:+.2f}%", positive=total_daily >= 0)

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════
    #  PER-MARKET BREAKDOWN  (native currencies)
    # ════════════════════════════════════════════════════════════════
    st.markdown("### Breakdown by Market")

    def fmt_inr_plain(v):
        try: return f"\u20b9{float(v):,.2f}"
        except: return "\u2014"
    def fmt_inr_signed(v):
        try:
            v = float(v)
            return f"+\u20b9{v:,.2f}" if v >= 0 else f"-\u20b9{abs(v):,.2f}"
        except: return "\u2014"
    def fmt_usd_plain(v):
        try: return f"${float(v):,.2f}"
        except: return "\u2014"
    def fmt_usd_signed(v):
        try:
            v = float(v)
            return f"+${v:,.2f}" if v >= 0 else f"-${abs(v):,.2f}"
        except: return "\u2014"

    # India — INR
    india_pnl     = india_current_inr - india_invested_inr
    india_pnl_pct = (india_pnl / india_invested_inr * 100) if india_invested_inr else 0
    with st.expander(
        f"\U0001f1ee\U0001f1f3 India (Angel One)  |  {fmt_inr_plain(india_current_inr)}  "
        f"{(chr(43) if india_pnl >= 0 else chr(45))}{india_pnl_pct:.1f}%",
        expanded=True,
    ):
        c1, c2, c3, c4 = st.columns(4)
        with c1: dash_metric("Funds Added (INR)",   fmt_inr_plain(india_invested_inr))
        with c2: dash_metric("Current Value (INR)",  fmt_inr_plain(india_current_inr))
        with c3: dash_metric("P&L",                  fmt_inr_signed(india_pnl),
                              f"{india_pnl_pct:+.2f}%", positive=india_pnl >= 0)
        with c4: dash_metric("Today's Change",      fmt_inr_signed(india_daily_inr_val),
                              f"{india_daily_pct:+.2f}%", positive=india_daily_inr_val >= 0)

    # US — USD
    us_pnl     = us_current_usd - us_invested_usd
    us_pnl_pct = (us_pnl / us_invested_usd * 100) if us_invested_usd else 0
    with st.expander(
        f"\U0001f1fa\U0001f1f8 US (Vested)  |  {fmt_usd_plain(us_current_usd)}  "
        f"{(chr(43) if us_pnl >= 0 else chr(45))}{us_pnl_pct:.1f}%",
        expanded=True,
    ):
        c1, c2, c3, c4 = st.columns(4)
        with c1: dash_metric("Deposited (USD)",     fmt_usd_plain(us_invested_usd))
        with c2: dash_metric("Current Value (USD)",  fmt_usd_plain(us_current_usd))
        with c3: dash_metric("P&L",                  fmt_usd_signed(us_pnl),
                              f"{us_pnl_pct:+.2f}%", positive=us_pnl >= 0)
        with c4: dash_metric("Today's Change",      fmt_usd_signed(us_daily_usd),
                              f"{us_daily_pct:+.2f}%", positive=us_daily_usd >= 0)

    # UK — SGD
    uk_pnl     = uk_current_sgd - uk_invested_sgd
    uk_pnl_pct = (uk_pnl / uk_invested_sgd * 100) if uk_invested_sgd else 0
    with st.expander(
        f"\U0001f1ec\U0001f1e7 UK (JP Morgan)  |  {fmt_sgd_plain(uk_current_sgd)}  "
        f"{(chr(43) if uk_pnl >= 0 else chr(45))}{uk_pnl_pct:.1f}%",
        expanded=True,
    ):
        c1, c2, c3, c4 = st.columns(4)
        with c1: dash_metric("Invested (SGD)",      fmt_sgd_plain(uk_invested_sgd))
        with c2: dash_metric("Current Value (SGD)", fmt_sgd_plain(uk_current_sgd))
        with c3: dash_metric("P&L",                 fmt_sgd_signed(uk_pnl),
                              f"{uk_pnl_pct:+.2f}%", positive=uk_pnl >= 0)
        with c4: dash_metric("Today's Change",     fmt_sgd_signed(uk_daily_sgd),
                              f"{uk_daily_pct:+.2f}%", positive=uk_daily_sgd >= 0)

    # ════════════════════════════════════════════════════════════════
    #  FX RATES
    # ════════════════════════════════════════════════════════════════
    st.markdown("---")
    fx1, fx2, fx3, fx4 = st.columns(4)
    with fx1: dash_metric("USD / SGD",    f"S${usd_sgd:.4f}")
    with fx2: dash_metric("GBP / SGD",    f"S${gbp_sgd:.4f}")
    with fx3: dash_metric("INR / SGD",    f"S${inr_sgd:.5f}")
    with fx4: dash_metric("Last Updated", datetime.now().strftime("%H:%M:%S"))
