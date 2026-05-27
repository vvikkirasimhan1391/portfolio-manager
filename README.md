# 📊 Portfolio Manager — Venkat

A Streamlit dashboard to track your investments across India (Angel One), US (Vested), and UK (JP Morgan Workplace Solutions).

---

## 🚀 Quick Start

### 1. Install Python
Make sure you have **Python 3.9 or later** installed.
Download from: https://www.python.org/downloads/

### 2. Open Terminal / Command Prompt
Navigate to this folder:
```
cd "C:\Users\LENOVO\Documents\Claude\Projects\portfolio manager"
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Run the app
```
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

---

## ⚙️ First-time Setup

### Angel One (India)
1. Log in to https://smartapi.angelbroking.com/
2. Click **Create App** → give it a name → save
3. Copy the **API Key**
4. Your **Client ID** = your Angel One login ID (e.g. A12345)
5. Your **Password** = your Angel One trading PIN
6. **TOTP Secret**: Open Angel One mobile app → Profile → Settings → Security → Enable TOTP → Copy the secret key shown

Then go to **⚙️ Settings** in the app and paste these credentials.

### Vested Finance (US Stocks)
Vested does not provide a public API. In the **🇺🇸 US** tab:
- Add your holdings manually (ticker, quantity, average buy price in USD)
- OR export a CSV from Vested and import it

CSV format required: `ticker, qty, avg_price_usd, name, sector, buy_date`

### JP Morgan Workplace Solutions (UK Stocks)
JP Morgan WPS does not provide a public API. In the **🇬🇧 UK** tab:
- Add your holdings manually (ticker with `.L` suffix, quantity, average buy price in GBP)
- OR export a CSV and import it

**UK ticker format:** Use `.L` suffix for LSE stocks, e.g.:
- Lloyds Banking → `LLOY.L`
- BP → `BP.L`
- Shell → `SHEL.L`
- Barclays → `BARC.L`

CSV format required: `ticker, qty, avg_price_gbp, name, sector, buy_date`

---

## 📁 File Structure

```
portfolio manager/
├── app.py                  ← Main Streamlit app
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
├── utils/
│   ├── angel_api.py        ← Angel One API integration
│   └── price_fetcher.py    ← yfinance price & FX fetching
└── data/                   ← Created automatically
    ├── settings.json       ← Your API credentials (stored locally)
    ├── us_holdings.json    ← US holdings data
    └── uk_holdings.json    ← UK holdings data
```

---

## 🔄 Prices & Refresh

- Prices are fetched from **Yahoo Finance** and cached for **5 minutes**
- Click **🔄 Refresh Prices** in the sidebar to force an update
- Angel One data requires a manual **Connect & Fetch** click (TOTP is time-sensitive)
- FX rates (USD/INR, GBP/INR) are also fetched live from Yahoo Finance

---

## 🔒 Security Note

Your Angel One credentials are stored in `data/settings.json` on your local machine only. They are never sent anywhere except directly to the Angel One API. Keep this file private and do not share it.

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| Angel One login fails | Check credentials in Settings; regenerate TOTP secret if needed |
| Price shows `—` | Ticker may be wrong or market closed; verify on Yahoo Finance |
| UK price looks wrong | LSE prices are sometimes in pence — the app auto-converts if > 500 |
| App won't start | Make sure you're in the right folder and Python ≥ 3.9 |
