# components.py
from dash import html, dcc

def inline_input(label_text, input_id, input_type, value=None, step=None):
    return html.Div([
        html.Label(label_text, htmlFor=input_id),
        dcc.Input(id=input_id, type=input_type, value=value, step=step)
    ])