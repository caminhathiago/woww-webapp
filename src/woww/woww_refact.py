from datetime import datetime, timedelta, timezone

from pydantic import validate_call

import pandas as pd
import numpy as np
import xarray as xr

import plotly.graph_objects as go



class MaritimeOperation:
    
    @validate_call
    def __init__(self, 
                 thgt_limit:float,
                 tper_limit:float,
                 start_datetime:datetime,
                 duration:timedelta,
                 first_contingency_factor:float,
                 second_contingency_factor:float):

        self.thgt_limit = thgt_limit
        self.tper_limit = tper_limit
        if start_datetime.tzinfo is None:
            self.start_datetime = start_datetime.replace(tzinfo=timezone.utc)
        else:
            self.start_datetime = start_datetime.astimezone(timezone.utc)
        self.duration = duration
        self.first_contingency_factor = first_contingency_factor
        self.second_contingency_factor = second_contingency_factor

    @property
    def contingency_time(self) -> timedelta:
        if self.first_contingency_factor < 1:
            raise ValueError("Contingency factor must be equal or greater than 1.")
        else:
            return self.duration * self.first_contingency_factor
        
    @property
    def time_reference(self) -> timedelta:
        return self.duration + self.contingency_time
    
    @property
    def estimated_end_datetime(self) -> datetime:
        return self.start_datetime + self.time_reference


class ForecastData:
    @validate_call
    def __init__(self, forecast_data:str):
        self._forecast_data_file_name = forecast_data

    @property
    def data(self) -> pd.DataFrame:
        data = pd.read_csv(self._forecast_data_file_name)
        time_col, _ = ForecastData.find_datetime_column(data)
        data[time_col] = pd.to_datetime(data[time_col])
        return data

    @property
    def last_issuance(self) -> datetime:
        _, time_data = ForecastData.find_datetime_column(self.data)
        return time_data.min().to_pydatetime()
    
    @property
    def forecast_time_range(self) -> tuple[pd.Timestamp, pd.Timestamp]:
        return ForecastData.get_time_range(self.data)

    @staticmethod
    def get_time_range(data:pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
        _, time_data = ForecastData.find_datetime_column(data)
        return time_data.min(), time_data.max()

    @staticmethod
    def find_datetime_column(data:pd.DataFrame) -> tuple[str, pd.Series]:
        for col in data.columns:
            col_data = data[col]
            if pd.api.types.is_datetime64_any_dtype(col_data):
                return col, col_data
            try:
                parsed = pd.to_datetime(col_data, errors='raise')
                return col, parsed
            except (ValueError, TypeError):
                continue
        raise ValueError("No datetime-like column found in the DataFrame.")



class Analysis:
    @validate_call(config={"arbitrary_types_allowed": True})
    def __init__(self, operation:MaritimeOperation, forecast:ForecastData):
        self.operation = operation
        self.forecast = forecast
        self._validate_operation_time()

    @property
    def time_from_last_isuance(self):
        return self.operation.start_datetime - self.forecast.last_issuance

    def _validate_operation_time(self):
        op_time = self.operation.start_datetime
        forecast_start, forecast_end = self.forecast.forecast_time_range
        if not(forecast_start <= op_time <= forecast_end):
            raise ValueError(
                f"Operation start time {op_time.isoformat()} is outside forecast range "
                f"{forecast_start.isoformat()} to {forecast_end.isoformat()}"
            )

    @property
    def _discrete_wowws(self) -> pd.DataFrame:
        data = self.forecast.data.copy()
        
        limits_mask = ((data['thgt'] <= self.operation.thgt_limit) &
                (data['tper'] <= self.operation.tper_limit)
            )
        
        data['discrete_woww'] = False
        if not limits_mask.empty:
            data.loc[limits_mask, 'discrete_woww'] = True

        return data
    
    @property
    def _continuous_wowws(self) -> pd.DataFrame:
        
        rolling_class = self._discrete_wowws.copy()
        
        rolling_workable = (
            rolling_class.set_index('date_time')
            ['discrete_woww'].rolling(window=self.operation.duration)
            .apply(lambda x: x.all(), raw=True)
        )
        rolling_class["continuos_woww"] = rolling_workable.reset_index()['discrete_woww'] == 1.0        

        return rolling_class

    @property
    def data_wowws(self) -> pd.DataFrame:
        
        id_wowws_data = self._continuous_wowws.copy()
        
        is_new_block = (id_wowws_data['continuos_woww'] & ~id_wowws_data['continuos_woww'].shift(fill_value=False)).astype(int)
        id_wowws_data['woww_id'] = is_new_block.cumsum()

        id_wowws_data.loc[~id_wowws_data['continuos_woww'], 'woww_id'] = 0

        return id_wowws_data
    
    @property
    def wowws(self) -> pd.DataFrame:
        wowws = self.data_wowws.copy()
        wowws = (wowws
                    .groupby('woww_id')['date_time']
                    .agg(start_date='min', end_date='max')
                    )
        wowws['duration_d'] = Analysis.calculate_duration(wowws, format='days')
        wowws['duration_h'] = Analysis.calculate_duration(wowws, format='hours')
        wowws['duration_hhmm'] = Analysis.calculate_duration(wowws, format='hours_minutes')
        wowws = wowws.drop(0)
        return wowws

    @staticmethod
    def calculate_duration(data:pd.DataFrame, format:str) -> pd.Series:
        duration = data['end_date'] - data['start_date']
        if format == 'days':
            pass
        elif format == 'hours':
            duration = duration.dt.total_seconds() / 3600
        elif format == 'hours_minutes':
            duration = duration.apply(Analysis.format_timedelta_to_hhmm)
        return duration

    @staticmethod
    def format_timedelta_to_hhmm(td:timedelta) -> str:
        total_minutes = int(td.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"
         
        
        return duration

    @staticmethod
    def calculate_duration_hours(data:pd.DataFrame) -> pd.Series:
        return data['end_date'] - data['start_date']



class Plot:
    @validate_call(config={"arbitrary_types_allowed": True})
    def __init__(self, analysis):
        self.analysis = analysis
        self.operation = self.analysis.operation

    def plot_wowws_timeseries(self) -> None:
        fig = go.Figure()

        data = self.analysis.data_wowws
        wowws = self.analysis.wowws

        # Primary y-axis trace (value)
        fig.add_trace(go.Scatter(
            x=data['date_time'], y=data['thgt'], 
            mode='lines', name='Value',
            yaxis='y1'
        ))

        # Secondary y-axis trace (tper)
        fig.add_trace(go.Scatter(
            x=data['date_time'], y=data['tper'], 
            mode='lines', name='Tper',
            yaxis='y2'
        ))

        # Add vertical highlight regions
        for idx, row in wowws.iterrows():
            fig.add_vrect(
                x0=row['start_date'], x1=row['end_date'],
                fillcolor="green", opacity=0.3,
                layer="below", line_width=0,
                annotation_text=f"WOWW {idx}",
                annotation_position="top left",
                annotation=dict(font=dict(color="white"))
            )

        # Operation period highlight
        fig.add_vrect(
            x0=self.operation.start_datetime, 
            x1=self.operation.estimated_end_datetime, 
            fillcolor="blue", opacity=0.3,
            layer="below", line_width=0,
            annotation_text=f"OPERATION",
            annotation_position="top right",
            annotation=dict(font=dict(color="white"))
        )

        # Layout update for dual y-axes and styling
        fig.update_layout(
            # title=dict(text="Time Series with Highlights and Twin Y-Axis", font=dict(color='white')),
            font=dict(color='white'),  # General font color
            height=200,  # match the container height
            margin=dict(l=0, r=0, t=0, b=0),  # remove all outer space
            xaxis=dict(
                # title=dict(text='Time', font=dict(color='white')),
                tickfont=dict(color='white'),
                color='white'
            ),
            yaxis=dict(
                title=dict(text='Hs (m)', font=dict(color='white')),
                side='left',
                showgrid=True,
                zeroline=False,
                tickfont=dict(color='white'),
                color='white'
            ),
            yaxis2=dict(
                title=dict(text='Tp (s)', font=dict(color='white')),
                overlaying='y',
                side='right',
                showgrid=False,
                zeroline=False,
                tickfont=dict(color='white'),
                color='white'
            ),
            legend=dict(
                x=0.01, y=0.99,
                font=dict(color='white')
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(255, 255, 255, 0.1)'
        )

        return fig
 
    
    
class StatsTable:
    @validate_call(config={"arbitrary_types_allowed": True})
    def __init__(self, analysis):
        self.analysis = analysis

    @property
    def global_stats(self) -> pd.DataFrame:
        return self.analysis.wowws[['thgt', 'tper', 'tdir']].describe().round(2)
    
    @property
    def per_woww_stats(self) -> pd.DataFrame:
        return self.analysis.wowws.groupby('woww_id').describe().T.loc[['thgt', 'tper', 'tdir']]

class Dashboard:
    pass


if __name__ == "__main__":

    mo = MaritimeOperation(
                thgt_limit=5,
                 tper_limit=16.,
                 start_datetime=datetime(2025,6,1,10,0,0),
                 duration=timedelta(hours=5),
                 first_contingency_factor=1.1,
                 second_contingency_factor=1.2,
    )


    fd = ForecastData(forecast_data="data/ww3_LAT-32_LON115.csv")

    a = Analysis(mo, fd)

    p = Plot(a)
    # p.plot_wowws_timeseries()


    print("script finished")
