import sys
import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))



import dash
from dash import html, dcc, callback_context
import dash_leaflet as dl
from dash.dependencies import Input, Output, State
from datetime import datetime, timedelta
import numpy as np
import plotly.graph_objs as go
from src.woww.api.erddap import ErddapData
from woww.process.erddap import WW3Processor
from src.woww.woww_refact import *




app = dash.Dash(__name__)
app.title = "Workable Weather Window Dashboard"

default_lat = -32
default_lon = 115
default_start = "2025-05-31 00:49:51"  # empty default
default_duration = "1"
default_fcf = "1"
default_scf = "1"

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Roboto', sans-serif;
                font-size: 10px;
                margin: 0;
                padding: 0;
            }
            label {
                font-weight: 500;
                margin-right: 6px;
                font-size: 9px;
            }
            input {
                font-size: 9px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

def inline_input(label_text, input_id, input_type, value=None, step=None):
    return html.Div([
        html.Label(label_text, htmlFor=input_id,  style={"width": "45%", "fontSize": "11px",  "marginRight": "0px" }),
        dcc.Input(id=input_id, type=input_type, value=value, step=step,
                  style={"width": "50%", "fontSize": "11px",  "backgroundColor": "rgba(255, 255, 255, 0.3)", "borderRadius": "3px"})
    ], style={"display": "flex", "alignItems": "center", "marginBottom": "4px"})

app.layout = html.Div([
    # Floating Input Box
    html.Div([
        html.H3("Workable Weather Window Analysis", style={"margin-bottom": "15px", "fontSize": "14px" }),
        html.H5("Maritime Operation Settings", style={"margin-top": "0", "color": "#333","fontSize": "12px" }),

        inline_input("Latitude:", "lat-input", "number", value=default_lat, step=1),
        inline_input("Longitude:", "lon-input", "number", value=default_lon, step=1),
        inline_input("Start:", "start-input", "text", value=default_start),
        inline_input("Duration (h):", "duration-input", "number", value=default_duration, step=0.1),
        inline_input("Hs Limit:", "hs-limit-input", "number", value=default_fcf, step=0.1),
        inline_input("Tp Limit:", "tp-limit-input", "number", value=default_fcf, step=0.1),
        inline_input("1st Cont Factor:", "fcf-input", "number", value=default_fcf, step=0.1),
        inline_input("2nd Cont Factor:", "scf-input", "number", value=default_scf, step=0.1),

        dcc.Loading([html.Div(id="forecast-loader")], type="circle"),

        html.Button(
            "Extracting Forecast",
            id="generate-button",
            disabled=True,
            style={"display": "none", "marginTop": "10px", "width": "100%"}
        ),

        dcc.Store(id="forecast-ready", data=False),

    ], style={
    "position": "absolute",
    "top": "10px",
    "left": "10px",
    "backgroundColor": "rgba(255, 255, 255, 0.3)",
    "padding": "12px",
    "borderRadius": "0px",
    "zIndex": "1001",
    "boxShadow": "0 3px 6px rgba(0, 0, 0, 0.15)",
    "width": "240px",
    "fontFamily": "Roboto, sans-serif",
    "maxHeight": "90vh",
    "overflowY": "auto",
}),

   html.Div([
    dcc.Graph(
        id="timeseries-plot",
        config={"displayModeBar": False},
        style={"height": "320px", "width": "980px"}  # Graph size
    )
], id="plot-container", style={
    "position": "fixed",         # Fixed to the viewport
    "bottom": "0px",             # Stick to the bottom
    "left": "0px",               # Stick to the left
    "zIndex": "1000",
    "display": "none",
    "boxShadow": "0 -2px 8px rgba(0,0,0,0.2)",  # Optional visual polish
    "backgroundColor": "white"  # Optional background to prevent overlay transparency issues
}),
 
    # Leaflet Map
    dl.Map(
        id="map",
        center=[default_lat, default_lon],
        zoom=7,
        zoomControl=False,
        children=[
            dl.TileLayer(
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attribution='Tiles © Esri'
            ),
            dl.ZoomControl(position="topright"),
            dl.Marker(id="marker", position=[default_lat, default_lon], draggable=False,
                      icon=dict(
                        iconUrl="/assets/boat_335060.png",
                        # shadowUrl="https://leafletjs.com/examples/custom-icons/leaf-shadow.png",
                        iconSize=[30, 40],
                        # shadowSize=[50, 64],
                        iconAnchor=[15, 20],
                        # shadowAnchor=[4, 62],
                        popupAnchor=[-3, -76],
                            ))
                            ],
        style={"width": "100vw", "height": "100vh", "position": "fixed", "zIndex": "1"}
    ),
])


@app.callback(
    Output("lat-input", "value"),
    Output("lon-input", "value"),
    Output("map", "center"),
    Output("marker", "position"),
    Input("lat-input", "value"),
    Input("lon-input", "value"),
    Input("map", "click_lat_lng"),
    Input("marker", "n_dragend"),
    Input("marker", "position"),
)
def sync_marker_and_inputs(lat_input, lon_input, click_lat_lng, n_dragend, marker_pos):
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "lat-input" or triggered_id == "lon-input":
        return lat_input, lon_input, [lat_input, lon_input], [lat_input, lon_input]

    elif triggered_id == "map" and click_lat_lng:
        lat, lon = click_lat_lng
        return lat, lon, [lat, lon], [lat, lon]

    elif triggered_id == "marker" and n_dragend:
        lat, lon = marker_pos
        return lat, lon, [lat, lon], [lat, lon]

    return lat_input, lon_input, [lat_input, lon_input], [lat_input, lon_input]

@app.callback(
    Output("forecast-ready", "data"),
    Output("forecast-loader", "children"),
    Input("lat-input", "value"),
    Input("lon-input", "value"),
)
def fetch_forecast(lat, lon):
    # import time
    # time.sleep(2)  
    if not os.path.exists(f"data/ww3_LAT{lat}_LON{lon}.csv"):
        wd_ww3 = ErddapData(server="https://pae-paha.pacioos.hawaii.edu/erddap/",
                            protocol="griddap",
                            dataset_id="ww3_global",
                            initialize=True)
        
        wd_ww3.set_vars_constraints(variables=['Tdir', 'Tper', 'Thgt'],
                                        # 'sdir','sper','shgt',s
                                        # 'wdir','wper','whgt'],
                            longitude=lon,#(305,333),
                            latitude=lat,#(-35,4),
                            start_date=(datetime.now()-timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            correct_pos=False)

        data = wd_ww3.grab_batch_data(response_type="pandas")

        data = WW3Processor.process_var_labels(data)
        data = WW3Processor.rename_var_labels(data)
        data = WW3Processor.process_datetime(data)
        data = WW3Processor.get_direc_quadrant(data=data)

        data.to_csv(f"data/ww3_LAT{lat}_LON{lon}.csv")

    return True, ""  # Nothing to display in forecast-loader


@app.callback(
    Output("generate-button", "style"),
    Output("generate-button", "children"),
    Output("generate-button", "disabled"),
    Input("forecast-ready", "data")
)
def update_generate_button(forecast_ready):
    if forecast_ready:
        return {"display": "block", "marginTop": "10px", "width": "100%", "backgroundColor": "rgba(12.94, 39.22, 46.67, 1)", "color": "white"}, "Generate", False
    else:
        return {"display": "block", "marginTop": "10px", "width": "100%"}, "Extracting Forecast...", True

@app.callback(
    Output("timeseries-plot", "figure"),
    Output("plot-container", "style"),
    Input("generate-button", "n_clicks"),
    State("lat-input", "value"),
    State("lon-input", "value"),
    State("start-input", "value"),
    State("duration-input", "value"),
    State("hs-limit-input", "value"),
    State("tp-limit-input", "value"),
    State("fcf-input", "value"),
    # add other inputs if needed
)
def generate_plot(n_clicks, lat, lon, start, duration, hs_limit, tp_limit, fcf):
    if not n_clicks or n_clicks == 0:
        # No clicks yet: return empty plot and hide container
        return go.Figure(), {"display": "none"}

    # Validate inputs (same as your current logic)
    if None in [lat, lon, start, duration, fcf] or start == "" or duration == "" or fcf == "":
        return go.Figure(), {"display": "none"}

    try:
        duration = float(duration)
        fcf = float(fcf)
    except ValueError:
        return go.Figure(), {"display": "none"}

    try:
        start_dt = datetime.fromisoformat(start.strip())
    except Exception:
        return go.Figure(), {"display": "none"}

    # times = [start_dt + timedelta(hours=i) for i in range(int(duration)+1)]

    # data = np.sin(np.linspace(0, 3 * np.pi, len(times))) * fcf + np.random.normal(scale=0.2, size=len(times))
    # import pandas as pd
    # data = pd.read_csv(f"data/ww3_LAT{lat}_LON{lon}.csv")

    # fig = go.Figure(
    #     data=[go.Scatter(x=data['date_time'], y=data['thgt'], mode='lines+markers', name='Random Data')],
    #     layout=go.Layout(
    #         xaxis_title="Time",
    #         yaxis_title="Value",
    #         template="plotly_white",
    #         margin=dict(l=30, r=20, t=40, b=30)
    #     )
    # )

    start_datetime = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")

    mo = MaritimeOperation(
                thgt_limit=hs_limit,
                 tper_limit=tp_limit,
                 start_datetime=start_datetime,
                 duration=timedelta(hours=duration),
                 first_contingency_factor=fcf,
                 second_contingency_factor=1.2,
    )


    fd = ForecastData(forecast_data=f"data/ww3_LAT{lat}_LON{lon}.csv")

    a = Analysis(mo, fd)

    p = Plot(a)
    fig = p.plot_wowws_timeseries()

    return fig, {
    "position": "fixed",  # stays anchored even on scroll
    "bottom": "0px",      # stick to the bottom
    "left": "0px",        # stick to the left
    "zIndex": "998",
    "width": "980px",
    "height": "420px",
    "display": "block",
}



if __name__ == "__main__":
    app.run(debug=True)
