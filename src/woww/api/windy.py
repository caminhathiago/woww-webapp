import os
import requests
from dotenv import load_dotenv

load_dotenv()

class WindyAPI:
    def __init__(self, api_key:str = None):
        if not api_key:
            self.api_key = os.getenv("WINDY_API_KEY")            
        else:
            self.api_key = api_key

        self.base_url = "https://api.windy.com/api/point-forecast/v2"

    def _compose_headers(self) -> dict:
        return {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def get_raw_data(self,
                lat: float,
                lon: float,
                model: str,
                levels: list,
                parameters: list) -> dict:

        payload = {
            "lat": lat,
            "lon": lon,
            "model": model,
            "levels": levels,
            "parameters": parameters,
            "key": self.api_key
        }

        return (requests
                .post(self.base_url,
                        headers=self._compose_headers(), 
                        json=payload)
                .json()
        )
