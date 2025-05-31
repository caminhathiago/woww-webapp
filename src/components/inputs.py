# components.py
from dash import html, dcc

def inline_input(label_text, input_id, input_type, value=None, step=None):
    return html.Div([
        html.Label(label_text, htmlFor=input_id,  style={"width": "45%", "fontSize": "11px",  "marginRight": "0px" }),
        dcc.Input(id=input_id, type=input_type, value=value, step=step,
                  style={"width": "50%", "fontSize": "11px",  "backgroundColor": "rgba(255, 255, 255, 0.3)", "borderRadius": "3px"})
    ], style={"display": "flex", "alignItems": "center", "marginBottom": "4px"})