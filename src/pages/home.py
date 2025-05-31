from datetime import datetime

from dash import html, dcc
import dash_leaflet as dl
from components.inputs import inline_input

default_lat = -32
default_lon = 115
default_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 2025-05-31 12:49:51 empty default
default_duration = "1"
default_fcf = "1"
default_scf = "1"


home_layout = html.Div([
    # Floating Input Box
    html.Div([
        html.H3("Workable Weather Window Analysis"),
        html.H5("Maritime Operation Settings"),

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
            disabled=True
        ),

        dcc.Store(id="forecast-ready", data=False),

    ], id="input-box"),

    html.Div([
        dcc.Graph(
            id="timeseries-plot",
            config={"displayModeBar": False}
        )
    ], id="plot-container"),

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
            dl.Marker(
                id="marker",
                position=[default_lat, default_lon],
                draggable=False,
                icon=dict(
                    iconUrl="assets/marker.png",
                    iconSize=[20, 20],
                    iconAnchor=[0, 20],
                    popupAnchor=[-3, -76]
                    # iconSize=[30, 40],
                    # iconAnchor=[15, 20],
                    # popupAnchor=[-3, -76]
                )
            )
        ]
    )
])