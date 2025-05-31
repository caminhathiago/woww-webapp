from dotenv import load_dotenv

from woww.api.windy import WindyAPI
from woww.data.process import WindyProcess
from woww.woww import WOWWAnalysis


def main():
    
    lat = -31.7567
    lon = 115.5447

    raw_data = windy_api.get_raw_data(lat=lat,
                                    lon=lon,
                                    model="gfsWave",
                                    levels=["surface"],
                                    parameters=["waves"])

    wp = WindyProcess()

    data = wp.converto_to_dataframe(raw_data)
    data = wp.rename_columns(data)
    data = wp.add_latlon(data, lat=lat, lon=lon)
    data = wp.time_to_datetime(data)
    data = wp.adjust_timezone(data)

    start_datetime, end_datetime = wp.extract_timerange(data)
    data.to_csv(f"output_path/windy_waves_forecast_{start_datetime}-{end_datetime}.csv")

    swvht_limit = 2
    tp_limit = 14
    wa = WOWWAnalysis(data=data, swvht_limit=swvht_limit, tp_limit=tp_limit)
    

    # ax = data.plot(subplots=True, figsize=(15, 5), marker="o")
    # import matplotlib.pyplot as plt
    # plt.tight_layout()  # optional, improves layout
    # plt.savefig("windy_plot.png")  # save to file
    # plt.close()  # release resources

    print("main ended")

if __name__ == "__main__":
    
    load_dotenv()
    
    windy_api = WindyAPI()

    main()

    print("script ended")

