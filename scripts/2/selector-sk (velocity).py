import numpy as np
import pandas as pd
import yfinance as yf

# 1. Selection des 60 actions
tickers = [
    # US (50)
    "NVDA", "MSFT", "AAPL", "GOOGL", "AMZN", "META", "AVGO", "AMD", "NFLX", "TSLA",
    "CRM", "ADBE", "ORCL", "NOW", "PANW", "CRWD", "UBER", "ANET", "LRCX", "KLAC",
    "AMAT", "MU", "QCOM", "INTU", "ISRG", "LLY", "REGN", "VRTX", "V", "MA",
    "COST", "LIN", "GE", "CAT", "PLTR", "APP", "JPM", "GS", "BRK-B", "CSCO",
    "XOM", "TMO", "ABBV", "WMT", "HD", "MCD", "NEE", "DE", "SPGI", "TJX",

    # Europe (25)
    "ASML.AS", "SAP.DE", "SIE.DE", "MC.PA", "RMS.PA", "OR.PA", "SU.PA", "AIR.PA", "SAF.PA", "NOVO-B.CO",
    "AZN.L", "REL.L", "LSEG.L", "RR.L", "RHM.DE", "ENR.DE", "IFX.DE", "ADYEN.AS", "RACE.MI", "UCG.MI",
    "ROG.SW", "NOVN.SW", "ALV.DE", "ITX.MC", "IBE.MC",

    # Asie-Pacifique (20)
    "2330.TW", "005930.KS", "000660.KS", "8035.T", "6857.T", "6861.T", "9984.T", "7203.T", "6758.T", "8306.T",
    "7974.T", "CSL.AX", "CBA.AX", "BHP.AX", "D05.SI", "0700.HK", "9988.HK", "1810.HK", "0388.HK", "2317.TW",

    # Canada (5)
    "SHOP.TO", "CSU.TO", "RY.TO", "ATD.TO", "CNQ.TO",
]

benchmark = "SPY"

# 2. Telechargement des donnees
data = yf.Tickers(
    tickers + [benchmark]
).history(
    period="3y",
    auto_adjust=True
)["Close"]

missing = [
    t for t in tickers + [benchmark]
    if t not in data.columns
]

if missing:
    raise ValueError(f"Missing data for: {missing}")

prices = data[tickers]
market = data[benchmark]

# 3. Rendements journaliers
returns = prices.pct_change(fill_method=None)
market_returns = market.pct_change(fill_method=None)

df = pd.DataFrame(index=tickers)

# 4. Momentum
df["momentum"] = (
    prices.shift(21).iloc[-1]
    / prices.shift(273).iloc[-1] - 1
)

# 5. Volatilite annualisee
df["volatility"] = (
    returns.tail(252).std() * np.sqrt(252)
)

# 6. Beta
betas = []

for ticker in tickers:

    concat_returns = pd.concat(
        [returns[ticker], market_returns],
        axis=1
    ).dropna().tail(252)

    if len(concat_returns) < 60:
        betas.append(np.nan)
        continue

    stock_ret = concat_returns.iloc[:, 0]
    bench_ret = concat_returns.iloc[:, 1]

    cov = np.cov(stock_ret, bench_ret, ddof=1)[0, 1]
    var_bench = np.var(bench_ret, ddof=1)

    beta = cov / var_bench if var_bench > 0 else np.nan

    betas.append(beta)

df["beta"] = betas

# 7. Endettement et ROE
debt = {}
roe = {}

for ticker in tickers:

    try:
        info = yf.Ticker(ticker).info

        debt[ticker] = info.get(
            "debtToEquity", np.nan
        )

        roe[ticker] = info.get(
            "returnOnEquity", np.nan
        )

    except Exception as e:
        print(f"Erreur pour {ticker}: {e}")
        debt[ticker] = np.nan
        roe[ticker] = np.nan

df["debt_to_equity"] = pd.Series(debt)
df["roe"] = pd.Series(roe)

# 8. Nettoyage des donnees
criteria = [
    "momentum",
    "volatility",
    "beta",
    "debt_to_equity",
    "roe"
]

df = df.replace([np.inf, -np.inf], np.nan)

print("\nValeurs manquantes :")
print(df[criteria].isna().sum())

# Exclure les entreprises avec indicateurs incomplets
df = df.dropna(subset=criteria).copy()

# Ecarter les ratios d'endettement negatifs
df = df[df["debt_to_equity"] >= 0].copy()

if len(df) < 25:
    raise ValueError(
        "Moins de 25 actions exploitables."
    )

# 9. Fonction Z-score amelioree
def zscore(series):

    series = series.astype(float)

    low = series.quantile(0.05)
    high = series.quantile(0.95)

    series = series.clip(
        lower=low,
        upper=high
    )

    std = series.std(ddof=0)

    if std == 0 or pd.isna(std):
        return pd.Series(0.0, index=series.index)

    return (series - series.mean()) / std

# 10. Calcul des Z-scores
df["z_momentum"] = zscore(df["momentum"])
df["z_volatility"] = zscore(df["volatility"])
df["z_beta"] = zscore(df["beta"])
df["z_debt"] = zscore(df["debt_to_equity"])
df["z_roe"] = zscore(df["roe"])

# 11. Score Velocity Fund
df["z_score"] = (
    0.35 * df["z_momentum"]
    - 0.20 * df["z_volatility"]
    - 0.10 * df["z_beta"]
    - 0.10 * df["z_debt"]
    + 0.25 * df["z_roe"]
)

# 12. Classement
df = df.sort_values(
    "z_score",
    ascending=False
)

print("\nCLASSEMENT DES ACTIONS")

print(df[[
    "momentum",
    "volatility",
    "beta",
    "debt_to_equity",
    "roe",
    "z_score"
]].round(4))

# 13. Selection des 25 meilleures actions
Velocity_25 = df.head(25)

print("\nTOP 25 Velocity FUND")
print(Velocity_25.index.tolist())