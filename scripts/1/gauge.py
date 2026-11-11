from pathlib import Path
import par84
import plotly.graph_objects as go

images = Path(par84.img_path)
name = "gauge-"

PORTFOLIO = "serenity"
Seuil_SHARPE = 1.00        

CFG = {
    "serenity": dict(sharpe=2.2258, color="#4fd1c0", fill="rgba(79,209,192,0.25)"),
    "velocity": dict(sharpe=2.7079, color="#ff3d6e", fill="rgba(255,61,110,0.25)"),
}
C = CFG[PORTFOLIO]

fig = go.Figure(layout=par84.layout)

fig.add_indicator(
    mode="gauge+number+delta",
    value=C["sharpe"],
    title={"text": "Ratio de Sharpe<br><span style='font-size:12px'>30 oct. 2023 → 29 oct. 2026</span><br> ",
    "font": {"size": 18}},
    number={"valueformat": ".2f", "font": {"color": C["color"]}},
    delta={"reference": Seuil_SHARPE, "valueformat": "+.2f", "suffix": " vs Seuil 1,0",
           "increasing": {"color": C["color"]}, "decreasing": {"color": "#f92672"}},
    domain={"x": [0, 1], "y": [0, 1]},
    gauge={
        "axis": {"range": [0, 3], "tickvals": [0, 1, 2, 3],
                 "tickwidth": 1, "tickcolor": "#aaaaaa"},
        "bar": {"color": C["color"]},
        "bgcolor": "rgba(10, 10, 20, 1)",
        "borderwidth": 2,
        "bordercolor": C["color"],
        "steps": [
            {"range": [0, 1], "color": "rgba(249, 38, 114, 0.25)"},
            {"range": [1, 2], "color": "rgba(255, 255, 255, 0.08)"},
            {"range": [2, 3], "color": C["fill"]},
        ],
        "threshold": {"line": {"color": "white", "width": 4},
                      "thickness": 0.8, "value": Seuil_SHARPE},
    },
)

fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font={"color": "white", "family": "Helvetica"},
    margin=dict(l=30, r=30, t=110, b=10),
)

fig.write_html(images / f"{name}1.html", config=par84.config)