
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import par84

# ==========================================
# 1. CONFIGURATION
# ==========================================

images = Path(par84.img_path)
images.mkdir(parents=True, exist_ok=True)

name = "marko-"

symbols = [
    "JNJ", "TTE.PA", "KO", "0002.HK", "0006.HK",
    "2914.T", "IBE.MC", "CB", "XOM", "BRK-B",
    "SHEL.L", "FTS.TO", "4502.T", "0066.HK", "ALV.DE",
    "0003.HK", "AAPL", "AI.PA", "TLS.AX", "9432.T",
    "ZURN.SW", "ED", "COST", "9433.T", "O"
]
symbols=sorted(symbols)
benchmark = "SPY"

# ==========================================
# 2. TELECHARGEMENT DES DONNEES
# ==========================================

data = yf.Tickers(
    symbols + [benchmark]
).history(
    period="3y",
    auto_adjust=True
)["Close"]

data.index = data.index.tz_localize(None)
data.index = data.index.normalize()

if data.index.has_duplicates:
    data = data.groupby(level=0).last()

missing_assets = [t for t in symbols + [benchmark] if t not in data.columns]
if missing_assets:
    raise ValueError(f"Cours manquants : {missing_assets}")

# Devises de cotation
currencies = {
    "JNJ": "USD",
    "TTE.PA": "EUR",
    "KO": "USD",
    "0002.HK": "HKD",
    "0006.HK": "HKD",
    "2914.T": "JPY",
    "IBE.MC": "EUR",
    "CB": "USD",
    "XOM": "USD",
    "BRK-B": "USD",
    "SHEL.L": "GBP",
    "FTS.TO": "CAD",
    "4502.T": "JPY",
    "0066.HK": "HKD",
    "ALV.DE": "EUR",
    "0003.HK": "HKD",
    "AAPL": "USD",
    "AI.PA": "EUR",
    "TLS.AX": "AUD",
    "9432.T": "JPY",
    "ZURN.SW": "CHF",
    "ED": "USD",
    "COST": "USD",
    "9433.T": "JPY",
    "O": "USD"
}

# Taux de change vers USD
fx_tickers = {
    "EUR": "EURUSD=X",
    "JPY": "JPYUSD=X",
    "AUD": "AUDUSD=X",
    "CHF": "CHFUSD=X",
    "GBP": "GBPUSD=X",
    "HKD": "HKDUSD=X",
    "CAD": "CADUSD=X"
}

fx_data = yf.Tickers(
    list(fx_tickers.values())
).history(
    period="3y",
    auto_adjust=True
)["Close"]

fx_data.index = fx_data.index.tz_localize(None)
fx_data.index = fx_data.index.normalize()

if fx_data.index.has_duplicates:
    fx_data = fx_data.groupby(level=0).last()

fx_data = fx_data.sort_index()

# ==========================================
# 3. CONVERSION DES PRIX EN USD
# ==========================================

prices_usd = pd.DataFrame(index=data.index)

for ticker in symbols:

    if ticker not in data.columns:
        raise ValueError(
            f"Action manquante : {ticker}"
        )

    currency = currencies[ticker]
    price = data[ticker]

    if currency == "USD":
        prices_usd[ticker] = price
        continue

    # Les actions britanniques sont cotees en pence
    if currency == "GBp":
        price = price / 100
        currency = "GBP"

    fx_symbol = fx_tickers[currency]

    if fx_symbol not in fx_data.columns:
        raise ValueError(
            f"Taux de change manquant : {fx_symbol}"
        )

    fx = fx_data[fx_symbol].reindex(
        data.index,
        method="ffill",
        limit=5
    )

    prices_usd[ticker] = price * fx

# Verification
print("\n==== Missing values ====")
print(prices_usd.isna().sum())

# ==========================================
# 4. HARMONISATION DES DATES
# ==========================================

# Utiliser les dates du benchmark SPY
market_prices = data[benchmark].dropna()

market_dates = market_prices.index

# Aligner les cours sur les jours de cotation US
df = prices_usd.ffill(limit=5).reindex(market_dates)

# Les cours des marches etrangers peuvent etre reportes
# lorsqu'ils sont fermes ; cette methode est une approximation.

# Supprimer uniquement les dates encore incompletes
df = df.dropna()

if len(df) < 252:
    raise ValueError(
        "Historique insuffisant pour les calculs."
    )

print("\nNombre de dates :", len(df))
print("Actions utilisees :", len(df.columns))

# ==========================================
# 5. COURS EN BASE 100
# ==========================================

print("\n==== Basis 100 ====")

df100 = df / df.iloc[0] * 100

print(df100)

fig = go.Figure(layout=par84.layout)

for ticker in symbols:
    fig.add_scatter(
        x=df100.index,
        y=df100[ticker],
        name=ticker
    )

fig.write_html(
    images / f"{name}1.html",
    config=par84.config
)

# ==========================================
# 6. RENDEMENTS JOURNALIERS
# ==========================================

print("\n==== Daily returns ====")

daily_returns = df.pct_change(
    fill_method=None
).dropna()

print(daily_returns)

fig = go.Figure(layout=par84.layout)

for ticker in symbols:
    fig.add_scatter(
        x=daily_returns.index,
        y=daily_returns[ticker],
        name=ticker
    )

fig.write_html(
    images / f"{name}2.html",
    config=par84.config
)

# Histogrammes
fig = go.Figure(layout=par84.layout)

for ticker in symbols:
    fig.add_histogram(
        x=daily_returns[ticker],
        name=ticker
    )

fig.write_html(
    images / f"{name}3.html",
    config=par84.config
)

# ==========================================
# 7. RENDEMENTS LOGARITHMIQUES
# ==========================================

log_returns = np.log(
    df / df.shift(1)
).dropna()

fig = go.Figure(layout=par84.layout)

for ticker in symbols:
    fig.add_scatter(
        x=log_returns.index,
        y=log_returns[ticker],
        name=ticker
    )

fig.update_layout(
    title="Logarithmic Daily Returns"
)

fig.write_html(
    images / f"{name}log.html",
    config=par84.config
)

# ==========================================
# 8. RENDEMENTS ANNUELS
# ==========================================

print("\n==== Annual returns ====")

mean_returns = daily_returns.mean() * 252

print(
    mean_returns.map(
        lambda x: f"{x:.2%}"
    )
)

# ==========================================
# 9. MATRICE DE COVARIANCE
# ==========================================

print("\n==== Covariance matrix ====")

cov_matrix = daily_returns.cov() * 252

print(cov_matrix)

# ==========================================
# 10. TAUX SANS RISQUE
# ==========================================

print("\n==== Risk-free rate ====")

rf_data = yf.Ticker("^IRX").history(
    period="5d"
)["Close"].dropna()

if rf_data.empty:
    raise ValueError(
        "Taux sans risque indisponible."
    )

rf = float(rf_data.iloc[-1]) / 100

print(f"{rf:.2%}")

# ==========================================
# 11. SIMULATION DE 10 000 PORTEFEUILLES
# ==========================================

np.random.seed(42)

num_portfolios = 10000

results = np.zeros(
    (num_portfolios, 3)
)

weights_list = []

for i in range(num_portfolios):

    weights = np.random.random(
        len(symbols)
    )

    weights /= np.sum(weights)

    w = pd.Series(
        weights,
        index=symbols
    )

    port_return = float(
        w @ mean_returns
    )

    port_volatility = float(
        np.sqrt(
            w @ cov_matrix @ w
        )
    )

    sharpe_ratio = (
        (port_return - rf) / port_volatility
        if port_volatility > 0 else np.nan
    )

    results[i, 0] = port_return
    results[i, 1] = port_volatility
    results[i, 2] = sharpe_ratio

    weights_list.append(weights)

results = pd.DataFrame(
    results,
    columns=[
        "Return",
        "Volatility",
        "Sharpe Ratio"
    ]
)

print("\n==== Simulation results ====")
print(results)

# ==========================================
# 12. PORTEFEUILLE AU SHARPE MAXIMAL
# ==========================================

max_sharpe_idx = (
    results["Sharpe Ratio"].idxmax()
)

max_sharpe_ratio = results.loc[
    max_sharpe_idx,
    "Sharpe Ratio"
]

best_weights = weights_list[
    max_sharpe_idx
]

w_best = pd.Series(
    best_weights,
    index=symbols
)

optimal_return = results.loc[
    max_sharpe_idx,
    "Return"
]

optimal_volatility = results.loc[
    max_sharpe_idx,
    "Volatility"
]

print("\n==== Optimal Portfolio ====")

print(f"Return : {optimal_return:.2%}")
print(f"Volatility : {optimal_volatility:.2%}")
print(f"Sharpe Ratio : {max_sharpe_ratio:.4f}")

# ==========================================
# 13. ALLOCATION OPTIMALE
# ==========================================

best_weights_df = pd.DataFrame({
    "Asset": symbols,
    "Weight": best_weights
})

print("\n==== Optimal weights ====")

print(
    best_weights_df.to_string(index=False)
)

fig = go.Figure(layout=par84.layout)

fig.add_pie(
    labels=symbols,
    values=best_weights,
    hole=0.45,
    textinfo="label+percent",
    textposition="inside",     
    insidetextorientation="radial",     
    hovertemplate="%{label} : %{percent}<extra></extra>",
)

fig.update_layout(
    title=None,                                   
    margin=dict(l=20, r=20, t=40, b=20),          
    legend=dict(font=dict(size=11), x=1.0, y=0.5),
)

fig.write_html(
    images / f"{name}4.html",
    config=par84.config
)

# ==========================================
# 14. BETA ET ALPHA DU PORTEFEUILLE
# ==========================================

print("\n==== Portfolio Beta and Alpha ====")

# Rendements du portefeuille
portfolio_returns = daily_returns @ w_best

# Rendements du benchmark SPY
spy_prices = market_prices.reindex(df.index)

spy_returns = spy_prices.pct_change(
    fill_method=None
).dropna()

# Alignement des dates
comparison = pd.concat(
    [
        portfolio_returns.rename("Portfolio"),
        spy_returns.rename("SPY")
    ],
    axis=1,
    join="inner",
    sort=False
).dropna()

if len(comparison) < 60:
    raise ValueError(
        "Donnees insuffisantes pour Beta et Alpha."
    )

# Beta
covariance = comparison[
    "Portfolio"
].cov(
    comparison["SPY"]
)

market_variance = comparison[
    "SPY"
].var()

if not np.isfinite(market_variance) or market_variance <= 0:
    raise ValueError(
        "Variance du marche invalide."
    )

beta = covariance / market_variance

# Rendements annualises
portfolio_annual_return = (
    comparison["Portfolio"].mean() * 252
)

market_annual_return = (
    comparison["SPY"].mean() * 252
)

# Alpha de Jensen
alpha = portfolio_annual_return - (
    rf + beta * (market_annual_return - rf)
)

print(f"Portfolio Beta : {beta:.4f}")
print(f"Portfolio Alpha : {alpha:.2%}")
print(f"Portfolio Annual Return : {portfolio_annual_return:.2%}")
print(f"S&P 500 Annual Return : {market_annual_return:.2%}")

# Export Beta et Alpha
beta_alpha_df = pd.DataFrame({
    "Indicator": [
        "Beta",
        "Alpha",
        "Portfolio Return",
        "S&P 500 Return"
    ],
    "Value": [
        beta,
        alpha,
        portfolio_annual_return,
        market_annual_return
    ]
})

beta_alpha_df.to_csv(
    images / f"{name}beta-alpha.csv",
    index=False
)

# ==========================================
# 15. GRAPHIQUE MARKOWITZ
# ==========================================

cml_x = np.linspace(
    0,
    results["Volatility"].max(),
    100
)

cml_y = (
    rf + max_sharpe_ratio * cml_x
)

fig = go.Figure(layout=par84.layout)

fig.add_scatter(
    x=results["Volatility"],
    y=results["Return"],
    mode="markers",
    name="Portefeuilles simulés",
    showlegend=False,           
    marker=dict(
        color=results["Sharpe Ratio"],
        colorscale="Viridis",
        size=5,                          
        opacity=0.7,
        showscale=True,
        colorbar=dict(
            title="Sharpe",
            x=1.02,                       
            len=0.8,
            thickness=14
        )
    ),
    text=[
        "<br>".join(
            f"{symbols[j]}: {weights_list[i][j]:.2%}"
            for j in range(len(symbols))
        )
        for i in range(num_portfolios)
    ],
    hovertemplate="Weights:<br>%{text}<extra></extra>"
)

fig.add_scatter(
    x=[optimal_volatility],
    y=[optimal_return],
    mode="markers",
    marker=dict(color="greenyellow", size=14),
    name="Max Sharpe"
)

fig.update_layout(
    title=None,                          
    xaxis_title="Annualized Volatility",
    yaxis_title="Annualized Return",
    legend=dict(
        orientation="h",                 
        x=0, y=-0.3
    ),
    margin=dict(l=60, r=20, t=40, b=90),    
    xaxis_range=[results["Volatility"].min() * 0.9, results["Volatility"].max() * 1.1],
    yaxis_range=[results["Return"].min() * 0.9, results["Return"].max() * 1.1],
)

fig.write_html(
    images / f"{name}5a.html",
    config=par84.config
)

fig.add_scatter(
    x=cml_x,
    y=cml_y,
    mode="lines",
    line=dict(dash="dash"),
    name="Estimated CML"
)

fig.write_html(
    images / f"{name}5b.html",
    config=par84.config
)

# ==========================================
# 16. CONTRIBUTION AU RISQUE
# ==========================================

marginal_contribution = (
    cov_matrix @ w_best
)

risk_contribution = (
    w_best * marginal_contribution
)

percent_contribution = (
    risk_contribution
    / (optimal_volatility ** 2)
)

fig = go.Figure(layout=par84.layout)

contrib = pd.Series(
    percent_contribution.values,
    index=symbols
).sort_values(ascending=False)

fig.add_bar(
    x=contrib.index,
    y=contrib.values,
    name="Risk Contribution",
    hovertemplate="%{x} : %{y:.2%}<extra></extra>"
)

fig.update_layout(
    title=None,                         
    xaxis_title=None,                  
    yaxis_title="Share of total variance",
    yaxis_tickformat=".0%",          
    xaxis_tickangle=-45,
    xaxis_tickfont_size=10,
    showlegend=False,
    margin=dict(l=60, r=20, t=40, b=70)  
)

fig.write_html(
    images / f"{name}6.html",
    config=par84.config
)

risk_contrib_table = pd.DataFrame({
    "Asset": symbols,
    "Weight": w_best.values,
    "Risk Contribution": percent_contribution.values
})

print("\n==== Contribution to risk ====")

print(
    risk_contrib_table.to_string(index=False)
)

# ==========================================
# 17. EXPORTATION
# ==========================================

best_weights_df.to_csv(
    images / f"{name}weights.csv",
    index=False
)

risk_contrib_table.to_csv(
    images / f"{name}risk-contribution.csv",
    index=False
)

print("\n==== ANALYSIS COMPLETED ====")
print("All charts and results have been saved.")

