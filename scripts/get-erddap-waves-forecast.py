from datetime import datetime, timedelta

import pandas as pd
from dotenv import load_dotenv

from woww.api.erddap import ErddapData
# from woww.data.process import WindyProcess
from woww.process.erddap import WW3Processor
# from woww.woww import WOWWAnalysis



def extract() -> pd.DataFrame:

    wd_ww3 = ErddapData(server="https://pae-paha.pacioos.hawaii.edu/erddap/",
                        protocol="griddap",
                        dataset_id="ww3_global",
                        initialize=True)
    
    wd_ww3.set_vars_constraints(variables=['Tdir', 'Tper', 'Thgt',
                                    'sdir','sper','shgt',
                                    'wdir','wper','whgt'],
                        longitude=115,#(305,333),
                        latitude=-31,#(-35,4),
                        start_date=(datetime.now()-timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        correct_pos=False)

    return wd_ww3.grab_batch_data(response_type="pandas")


def transform(data) -> pd.DataFrame:
    data = WW3Processor.process_var_labels(data)
    data = WW3Processor.rename_var_labels(data)
    data = WW3Processor.process_datetime(data)
    data = WW3Processor.get_direc_quadrant(data=data)

    return data

def load(data, file_name:str) -> None:
    data.to_csv(file_name)

    # ax = data.plot(subplots=True, figsize=(15, 15), marker="o")
    # import matplotlib.pyplot as plt
    # plt.tight_layout()  # optional, improves layout
    # plt.savefig("ww3_plot.png")  # save to file
    # plt.close()  # release resources


    # GFS ------------------------------

    # wd_gfs.set_vars_constraints(variables=['ugrd10m', 'vgrd10m'],
    #                     longitude=115,
    #                     latitude=-31,
    #             start_date=(datetime.now()-timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    #             correct_pos=False)

    # gfs = wd_gfs.grab_batch_data(response_type="pandas")

    # gfs = wd_gfs.process_var_labels(gfs)
    # gfs = wd_gfs.rename_var_labels(gfs)
    # gfs = gfs.set_index('date_time')
    # gfs = wd_gfs.select_vars(gfs)
    # gfs['wspd'] = wd_gfs.calc_wind_veloc(gfs)
    # gfs['wdir'] = wd_gfs.calc_wind_direc(gfs)


    # Saving pickles ---------------------
    # import pickle
    # with open("test/pickle_files/ww3.pkl", "wb") as f:
    #     pickle.dump(ww3, f)
    # with open("test/pickle_files/gfs.pkl", "wb") as f:
    #     pickle.dump(gfs, f)

    # # WOWW Analysis ------------------------
    # swvht_limit = 2
    # tper_limit = 14
    # wa = WOWWAnalysis(data=ww3,
    #                   tpop=4,
    #                   op_start= pd.Timedelta(2, 'H'),
    #                   wf_issuance=pd.Timedelta(2, 'H'),
    #                   swvht_limit=swvht_limit, 
    #                   tper_limit=tper_limit)



    print("main ended")

if __name__ == "__main__":
    
    load_dotenv()
    
    # data = extract()
    import pickle
    # with open('test/pickle_files/data.pkl', 'wb') as f:
    #     pickle.dump(data, f)
    with open('test/pickle_files/data.pkl', 'rb') as f:
        data = pickle.load(f)

    data = transform(data)
    load(data, "ww3.csv")

    print("script ended")

