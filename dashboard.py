import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import json
import os

app = dash.Dash(__name__)

# --- STYLING ---
BG_COLOR = "#0b0e11"  # Terminal Black
TEXT_COLOR = "#e1e1e1"
ACCENT_COLOR = "#00ffcc"  # Neon Mint

app.layout = html.Div(
    style={'backgroundColor': BG_COLOR, 'color': TEXT_COLOR, 'padding': '20px', 'fontFamily': 'Consolas, monospace'},
    children=[
        html.H1("ALPHA-FORGE: HFT EXECUTION MONITOR",
                style={'textAlign': 'center', 'color': ACCENT_COLOR, 'letterSpacing': '3px',
                       'borderBottom': f'1px solid {ACCENT_COLOR}', 'paddingBottom': '10px'}),

        # Live Stats Bar
        html.Div(id='live-stats',
                 style={'display': 'flex', 'justifyContent': 'space-around', 'fontSize': '18px',
                        'margin': '20px 0', 'padding': '20px', 'backgroundColor': '#1e222d', 'borderRadius': '5px',
                        'border': '1px solid #333'}),

        # Main Price and Signal Chart
        dcc.Graph(id='price-pos-graph', config={'displayModeBar': False}),

        html.Div(style={'height': '20px'}),  # Spacer

        # Equity Curve Chart (With Narrow Scaling)
        dcc.Graph(id='equity-graph', config={'displayModeBar': False}),

        # Update interval: 5 seconds
        dcc.Interval(id='interval-component', interval=5000, n_intervals=0)
    ])


@app.callback(
    [Output('price-pos-graph', 'figure'),
     Output('equity-graph', 'figure'),
     Output('live-stats', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    # 1. Safety Check: Ensure files exist before reading
    if not os.path.exists("live_trade_log.csv") or not os.path.exists("strategy_config.json"):
        return go.Figure(), go.Figure(), "INITIALIZING ENGINE: WAITING FOR DATA..."

    try:
        # 2. Read Logs (Limit to last 500 points for performance)
        df = pd.read_csv("live_trade_log.csv").tail(500)
        if df.empty:
            return go.Figure(), go.Figure(), "CONNECTING TO TRADE STREAM..."

        with open("strategy_config.json", "r") as f:
            conf = json.load(f)

        # 3. Price & Signals Figure
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=df['timestamp'], y=df['price'],
            name='Price', line=dict(color='#47a1ff', width=1.5)
        ))

        # Position Markers
        longs = df[df['pos'] == 1]
        shorts = df[df['pos'] == -1]

        fig1.add_trace(go.Scatter(
            x=longs['timestamp'], y=longs['price'], mode='markers',
            marker=dict(color='#00ff88', size=12, symbol='triangle-up'),
            name='Long Entry'
        ))

        fig1.add_trace(go.Scatter(
            x=shorts['timestamp'], y=shorts['price'], mode='markers',
            marker=dict(color='#ff4d4d', size=12, symbol='triangle-down'),
            name='Short Entry'
        ))

        fig1.update_layout(
            title="MARKET MICROSTRUCTURE & EXECUTION SIGNALS",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, rangeslider=dict(visible=False)),
            yaxis=dict(title="Price (USD)", gridcolor='#282c34', autorange=True),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=50, r=50, t=80, b=50)
        )

        # 4. Equity Curve Figure (NARROW SCALING IMPLEMENTED)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df['timestamp'], y=df['equity'],
            name='Equity', line=dict(color=ACCENT_COLOR, width=2.5),
            fill='tozeroy', fillcolor='rgba(0, 255, 204, 0.05)'
        ))

        # Calculate dynamic bounds for the Y-Axis
        e_min = df['equity'].min()
        e_max = df['equity'].max()
        e_range = e_max - e_min

        # Add a 5% "breathing room" buffer
        padding = e_range * 0.05 if e_range > 0 else 100

        fig2.update_layout(
            title="REAL-TIME CUMULATIVE EQUITY (SCALED)",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(
                title="Portfolio Value ($)",
                gridcolor='#282c34',
                # This narrows the scale to exactly where the action is
                range=[e_min - padding, e_max + padding],
                tickformat=".2f"
            ),
            margin=dict(l=50, r=50, t=80, b=50)
        )

        # 5. Header Stats Bar
        current_eq = df['equity'].iloc[-1]
        pnl_color = "#00ff88" if current_eq >= 100000 else "#ff4d4d"

        stats = [
            html.Div([html.Div("ACTIVE STRATEGY", style={'color': '#888', 'fontSize': '12px'}),
                      html.B(f"{conf.get('name', 'N/A')}", style={'color': ACCENT_COLOR})]),

            html.Div([html.Div("PARAMETERS", style={'color': '#888', 'fontSize': '12px'}),
                      html.B(f"P1: {conf.get('p1')} | P2: {conf.get('p2')}")]),

            html.Div([html.Div("BACKTEST SHARPE", style={'color': '#888', 'fontSize': '12px'}),
                      html.B(f"{conf.get('sr', 0):.2f}")]),

            html.Div([html.Div("LIVE PORTFOLIO VALUE", style={'color': '#888', 'fontSize': '12px'}),
                      html.B(f"${current_eq:,.2f}", style={'color': pnl_color})])
        ]

        return fig1, fig2, stats

    except Exception as e:
        # Standard logging for IB environments
        print(f"[DASHBOARD ERROR]: {e}")
        return go.Figure(), go.Figure(), "STREAMING ERROR: RECONNECTING..."


if __name__ == '__main__':
    # Using the updated 'run' method as required by Dash 2.11+
    app.run(debug=True, port=8050)