from pathlib import Path
import yfinance as yf
import par84
import plotly.graph_objects as go

symbol = 'TSLA'
images = Path(par84.img_path)
name = "2-"

df = yf.Ticker(symbol).history(period='1y', auto_adjust=True)
print(df.tail())

fig = go.Figure(layout=par84.layout)
fig.add_scatter(x=df.index, y=df.Close)
fig.write_html(images / f"{name}1.html", config=par84.config)

