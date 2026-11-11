import numpy as np
import pandas as pd
import yfinance as yf

# 1. Selection des 60 actions
tickers = [
    # US (41)
    "PG", "KO", "PEP", "WMT", "COST", "CL", "GIS", "KMB", "MDLZ", "HSY",
    "JNJ", "MRK", "UNH", "ABT", "MDT", "AMGN", "PFE", "LLY",
    "DUK", "NEE", "SO", "XEL", "AEP", "ED",
    "VZ", "T", "BRK-B", "CB",
    "MSFT", "AAPL", "CSCO", "GOOGL", "NVDA", "AMZN",
    "MCD", "LIN", "XOM", "O", "V", "ADP", "WM",

    # Europe (31)
    "NESN.SW", "NOVN.SW", "ROG.SW", "ZURN.SW",
    "BN.PA", "SAN.PA", "AI.PA", "OR.PA", "ORA.PA", "ENGI.PA", "TTE.PA", "MC.PA", "SU.PA",
    "ULVR.L", "AZN.L", "NG.L", "DGE.L", "GSK.L", "SSE.L", "REL.L", "SHEL.L",
    "DTE.DE", "ALV.DE", "MUV2.DE", "SAP.DE", "SIE.DE",
    "IBE.MC", "ENEL.MI", "ASML.AS", "AD.AS", "NOVO-B.CO",

    # Asie-Pacifique (23)
    "2914.T", "4502.T", "8766.T", "7203.T", "9433.T", "4452.T",
    "CSL.AX", "WOW.AX", "TLS.AX", "CBA.AX", "COL.AX", "BHP.AX",
    "D05.SI", "Z74.SI", "U11.SI",
    "0002.HK", "0006.HK", "0003.HK", "0066.HK",
    "2330.TW", "005930.KS", "2412.TW",

    # Canada (5)
    "FTS.TO", "ATD.TO", "BCE.TO", "L.TO", "RY.TO",
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

# 11. Score Serenity Fund
df["z_score"] = (
    0.25 * df["z_momentum"]
    - 0.35 * df["z_volatility"]
    - 0.15 * df["z_beta"]
    - 0.15 * df["z_debt"]
    + 0.10 * df["z_roe"]
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
serenity_25 = df.head(25)

print("\nTOP 25 SERENITY FUND")
print(serenity_25.index.tolist())