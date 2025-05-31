import os
import pandas as pd
import numpy as np

class WindyProcess:
    def __init__(self):
        self.data_parameters = ['waves_height-surface', 'waves_direction-surface', 'waves_period-surface']
        self.time_parameters = 'ts'

        self.cols_rename = {
            'waves_height-surface':"hs",
            'waves_direction-surface':"wvdir",
            'waves_period-surface':"tp",
            'ts':"time"
            }
    
    def converto_to_dataframe(self, data:dict) -> pd.DataFrame:
        values = np.array([data[param] for param in self.data_parameters]).T
        data = pd.DataFrame(values,
                            columns=self.data_parameters, 
                            index=data[self.time_parameters])
        data.index.name = self.cols_rename[self.time_parameters]
        return data
    
    def rename_columns(self, data:pd.DataFrame) -> pd.DataFrame:
        return data.rename(columns=self.cols_rename)

    def add_latlon(self, data:pd.DataFrame, lat:float, lon:float) -> pd.DataFrame:
        data["latitude"],  data["longitude"] = lat, lon
        return data

    def time_to_datetime(self, data: pd.DataFrame) -> pd.DataFrame:
        if self.time_parameters not in data.columns:
            time = data.index
        else:
            time = data[self.time_parameters]
        
        data.index = pd.to_datetime(time, unit="ms").tz_localize(tz="UTC")
        data.index.name = "datetime"
        return data.sort_index()
    
    def adjust_timezone(self, data:pd.DataFrame, offset:int = 8) -> pd.DataFrame:
        data.index = data.index.tz_convert(f"Etc/GMT-{offset}")
        return data
    
    def extract_timerange(self, data:pd.DataFrame) -> pd.DataFrame:
        return (data.index[0].strftime("%Y%m%d%H%M%S"),
                data.index[-1].strftime("%Y%m%d%H%M%S"))
    
    def round_data(data:pd.DataFrame) -> pd.DataFrame:
        return