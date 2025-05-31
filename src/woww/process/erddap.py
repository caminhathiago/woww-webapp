from datetime import datetime
from abc import ABC, abstractmethod

import pandas as pd
import numpy as np


class Processor(ABC):

    DIR_QUADRANTS = ['N', 'NNE', 'NE', 'ENE',
                        'E', 'ESE', 'SE', 'SSE',
                        'S', 'SSW', 'SW', 'WSW',
                        'W', 'WNW', 'NW', 'NNW']
    VARS_RENAME = {'time':'date_time',
                    'ugrd10m':'uw',
                    'vgrd10m': 'vw'}

    @staticmethod
    @abstractmethod
    def convert_to_datetime(data:pd.DataFrame) -> pd.DataFrame:
        pass

    @staticmethod
    @abstractmethod
    def process_var_labels(data:pd.DataFrame) -> pd.DataFrame:
        pass

    @staticmethod
    @abstractmethod
    def rename_var_labels(data:pd.DataFrame) -> pd.DataFrame:
        return data.rename(columns=Processor.VARS_RENAME)

    @staticmethod
    @abstractmethod
    def select_vars(data:pd.DataFrame) -> pd.DataFrame:
        pass

    @staticmethod
    @abstractmethod
    def get_direc_quadrant(data:pd.DataFrame) -> pd.DataFrame:
        pass


class GFSProcessor(Processor):
    
    VARS = ['date_time','latitude','longitude', 'uw','vw']

    @staticmethod
    def convert_to_datetime(data:pd.DataFrame) -> pd.DataFrame:
        pass

    @staticmethod
    def process_var_labels(data:pd.DataFrame) -> pd.DataFrame:
        data.columns = (data.columns
                .str.lower()
                .str.replace(r'\s+\(.*\)', '', regex=True)
                )
        return data

    @staticmethod
    def rename_var_labels(data:pd.DataFrame) -> pd.DataFrame:
        return data.rename(columns=Processor.VARS_RENAME)

    @staticmethod
    def select_vars(data:pd.DataFrame) -> pd.DataFrame:
        return data[[col for col in GFSProcessor.VARS if col in data.columns]]


    @staticmethod
    def get_direc_quadrant(data:pd.DataFrame) -> pd.DataFrame:
        
        direc_vars = [var for var in data.columns if "dir" in var.lower()]
        
        for direc_var in direc_vars:
            directional_var = data.filter(regex=direc_var)

            num_directions = len(Processor.DIR_QUADRANTS)
            degrees_per_direction = 360 / num_directions
            rotated_degrees = (directional_var + 11.25) % 360
            normalized_degrees = (rotated_degrees % 360 + 360) % 360

            direction_index = ((normalized_degrees // degrees_per_direction)
                                .astype(int, errors='ignore')
                                .squeeze()
                                )
            directions_map = {index: direction for index, direction in enumerate(Processor.DIR_QUADRANTS)}

            data[f'{direc_var}_quadrant'] = direction_index.map(directions_map)

        
        return data


    @staticmethod
    def calc_wind_veloc(data:pd.DataFrame) -> pd.DataFrame:
        return np.sqrt(data['uw']**2 + data['vw']**2)

    @staticmethod
    def calc_wind_direc(data:pd.DataFrame) -> pd.DataFrame:
        wind_direction = np.degrees(np.arctan2(data['vw'], data['uw']))
        wind_direction = (wind_direction + 360) % 360
        return wind_direction
    

class WW3Processor(Processor):
    
    VARS_RENAME = {'time':'date_time',
                                'ugrd10m':'uw',
                                'vgrd10m': 'vw'}

    VARS = ['date_time','latitude','longitude',
            'thgt','tdir','tper', 'uw','vw']

    @staticmethod
    def process_datetime(data:pd.DataFrame) -> pd.DataFrame:
        time_col = [col for col in data.columns if "time" in col.lower()]
        if time_col:
            data[time_col[0]] = pd.to_datetime(data[time_col[0]])
            return data.set_index(time_col[0])
        else:
            raise KeyError("No time variables found, please check time columns.")

    @staticmethod
    def process_var_labels(data:pd.DataFrame) -> pd.DataFrame:
        data.columns = (data.columns
                .str.lower()
                .str.replace(r'\s+\(.*\)', '', regex=True)
                )
        return data

    @staticmethod
    def rename_var_labels(data:pd.DataFrame) -> pd.DataFrame:
        return data.rename(columns=Processor.VARS_RENAME)


    @staticmethod
    def select_vars(data:pd.DataFrame) -> pd.DataFrame:
        return data[[col for col in WW3Processor.VARS if col in data.columns]]

    @staticmethod
    def get_direc_quadrant(data:pd.DataFrame) -> pd.DataFrame:
        
        direc_vars = [var for var in data.columns if "dir" in var.lower()]
        
        for direc_var in direc_vars:
            directional_var = data.filter(regex=direc_var)

            num_directions = len(Processor.DIR_QUADRANTS)
            degrees_per_direction = 360 / num_directions
            rotated_degrees = (directional_var + 11.25) % 360
            normalized_degrees = (rotated_degrees % 360 + 360) % 360

            direction_index = ((normalized_degrees // degrees_per_direction)
                                .astype(int, errors='ignore')
                                .squeeze()
                                )
            directions_map = {index: direction for index, direction in enumerate(Processor.DIR_QUADRANTS)}

            data[f'{direc_var}_quadrant'] = direction_index.map(directions_map)
        
        return data
