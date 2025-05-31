# callbacks.py
import os
from datetime import datetime, timedelta

from dash import callback_context
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

from woww.api.erddap import ErddapData
from woww.process.erddap import WW3Processor
from woww.woww_refact import MaritimeOperation, ForecastData, Analysis, Plot

def register_callbacks(app):
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
        "display": "block"
    }

    # @app.callback(
    # Output("mouse-coords", "children"),
    # Input("map", "mousemove"),
    # )
    # def update_mouse_coords(event):
        if event is None:
            return ""
        lat = event["latlng"]["lat"]
        lon = event["latlng"]["lng"]
        return f"Lat: {lat:.4f}, Lon: {lon:.4f}"