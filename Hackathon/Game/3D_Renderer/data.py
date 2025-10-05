import requests
import pandas as pd
import io
import json

class Data:
    latitude = 36.12
    longitude = 36.12
    date_start = 20240101
    date_end = 20241231
    responsepoint = None
    dataframe = None

    @classmethod
    def fetch_data(cls, lat, lon):
        cls.latitude = lat
        cls.longitude = lon  # fixed typo from 'longtitude' to 'longitude'

        url = (
            f"https://power.larc.nasa.gov/api/temporal/daily/point?"
            f"parameters=T2M,ALLSKY_SFC_SW_DWN,PRECTOTCORR,GWETTOP&community=ag&"
            f"longitude={cls.longitude}&latitude={cls.latitude}&"
            f"start={cls.date_start}&end={cls.date_end}&format=csv&units=metric&header=true&time-standard=utc"
        )
        print(f"Requesting data from URL:\n{url}")

        cls.responsepoint = requests.get(url)
        print(f"Request returned {cls.responsepoint.status_code}: '{cls.responsepoint.reason}'")

        if cls.responsepoint.status_code != 200:
            cls.dataframe = None
            raise RuntimeError("Failed to fetch data from NASA API")

        text = cls.responsepoint.text
        lines = text.splitlines()

        header_index = None
        for i, line in enumerate(lines):
            if line.startswith("YEAR"):
                header_index = i
                break

        if header_index is None:
            cls.dataframe = None
            raise RuntimeError("CSV header 'YEAR' not found")

        # Parse CSV data skipping rows before "YEAR"
        cls.dataframe = pd.read_csv(io.StringIO(text), skiprows=header_index)
        print(f"Data columns: {cls.dataframe.columns.tolist()}")
        return cls.dataframe

    @classmethod
    def export_dataframe_to_json(cls, filename="environment_data.json"):
        if cls.dataframe is None:
            raise RuntimeError("No data fetched to export.")
        data_list = cls.dataframe.to_dict(orient='records')
        try:
            with open(filename, "w") as json_file:
                json.dump(data_list, json_file, indent=4)
            print(f"Environment data exported to {filename}")
        except Exception as e:
            print(f"Failed to export data to JSON: {e}")