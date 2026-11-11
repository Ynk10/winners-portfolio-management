import numpy as np
import yfinance as yf
import scipy.stats as stats

symbol = "KO"

df = yf.Ticker(symbol).history(period='1y', auto_adjust=True)['Close']
print(df)

log_returns = np.log(df/df.shift(1)).dropna()
returns = df.pct_change().dropna()

def var1(log_returns, conf_level, horizon, investment):
    var = - investment * stats.norm.ppf(1-conf_level)*np.std(log_returns)*np.sqrt(horizon)
    print('VaR (parametric): $'+str(round(var,2)))
    
def var2(returns, conf_level, horizon, investment):
    rolling_returns = (1 + returns).rolling(horizon).apply(np.prod, raw=True) - 1
    rolling_returns = rolling_returns.dropna()
    var = -investment * np.percentile(rolling_returns, 100 * (1-conf_level))
    print('VaR (historic): $' +str(round(var, 2)))
    
conf_level = 0.99
horizon = 10
investment = 1000000

var1(log_returns, conf_level, horizon, investment)
var2(returns, conf_level, horizon, investment)
