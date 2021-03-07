import urllib.request
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline
from datetime import datetime
from datetime import date
import pandas as pd
import zipfile

month_list = ["jan", "feb", "mar", "avr", "may", "jun", "jul", "agu", "sep", "oct", "nov", "dec"]

#Download data from fide website
def download_file(month, year):
    try:
        url = f'http://ratings.fide.com/download/{month}{year[2:]}frl.zip'
        urllib.request.urlretrieve(url, f'dataset/{month}-{year}.zip')
    except:
        pass
    try:
        url = f'http://ratings.fide.com/download/standard_{month}{year[2:]}frl.zip'
        urllib.request.urlretrieve(url, f'dataset/{month}-{year}.zip')
    except:
        pass

def split_by_index(text, ind_list):
    out = []
    for pos in ind_list:
        cell = text[pos[0]:pos[1]]
        out.append(cell.strip())
    return out

def get_ind_list(first_row, month, year):
    print(type(first_row))
    first_row = first_row.lower()
    header_list = first_row.split()
    print(header_list)
    name_index = header_list.index("name")

    for col in header_list:
        for month in month_list:
            if month in col:
                elo_name = col
    print(elo_name)
    elo_index = header_list.index(elo_name)
    tit_pos = first_row.index("tit")
    positions = [[0, first_row.index("name")],
                  [first_row.index("name"), first_row.index(header_list[name_index+1])],
                  [first_row.index(elo_name)-1, first_row.index(header_list[elo_index+1])],
                [tit_pos, tit_pos+3]]
    print(positions)

    return positions

# convert one raw fide text file to dataframe
def convert2df(m, month, year):
    zip_name = f'dataset/{month}-{year}.zip'
    try:
        zf = zipfile.ZipFile(zip_name)  # having First.csv zipped file.
        file = zf.open(zf.namelist()[0])
    except:
        return pd.DataFrame([[]])
    #calculate date
    date_str = f"01/{m + 1}/{year}"
    date = datetime.strptime(date_str, '%d/%m/%Y').strftime('%d/%m/%Y')
    text = str(file.read())
    text = text[2:]
    rows = text.split("\\r\\n")
    first_row = rows[0]
    #in some cases there is no header
    if date in ["01/07/2003", "01/10/2003", "01/01/2004"]:
        first_row = "ID_NUMBER NAME                        TITLE COUNTRY JAN03 GAMES BIRTHDAY   FLAG"
    positions = get_ind_list(first_row, month, year)
    print(date)
    data_list = []
    for row in rows[1:]:
        data_list.append(split_by_index(row, positions))
    df = pd.DataFrame(data_list)
    df.rename(columns={0: 'id', 1: 'name', 2: 'elo',  3: 'title'}, inplace=True)
    df.elo = pd.to_numeric(df.elo, errors='coerce')
    print("missing", df["elo"].isnull().sum())
    df = df.dropna()
    df["elo"] = df["elo"].astype(float)
    #minimum elo value retained
    MIN_ELO = 2200
    df =df[df.elo>MIN_ELO]
    df["date"] = date
    print(df.head())
    return df

def download_df(month, year):
    download_file(month, year)
    df = convert2df(month, year)
    return df

#create the dataframe using all files
def collect_data(download=True):
    all_df = []
    for year in range(2000, 2022):
        for m, month in enumerate(month_list):
            if download:
                download_file(month, str(year))
            df = convert2df(m, month, str(year))
            if not df.empty:
                print(df.shape)
                all_df.append(df)
    hist_df = pd.concat(all_df)
    hist_df["title"] = hist_df["title"].str.lower()
    dict_tit = {'g': 'gm', 'wg': 'wgm', 'f': 'fm', 'wf': 'wfm', 'm': 'im', 'wm': 'wim', 'c': 'cm', 'c': 'cm'}
    list_tit = ['gm', 'im', 'fm', 'cm', 'wgm', 'wim', 'wfm', 'wcm']
    # replace using the dict
    hist_df = hist_df.replace({"title": dict_tit})
    # the title is erased if not in the dict
    hist_df.loc[~hist_df["title"].isin(list_tit), "title"] = ""
    hist_df.to_csv("processed_dataset/global.csv")



def process_players():
    file_name = "dataset/players_list_foa.txt"
    file = open(file_name, "r")
    rows = file.readlines()
    positions = [[0, 15], [15, 76], [76, 79], [152,158],[80, 82]]
    data_list = []
    for row in rows[1:]:
        data_list.append(split_by_index(row, positions))
    df = pd.DataFrame(data_list)
    df.rename(columns={0: 'id', 1: 'name', 2: 'country', 3: 'birth_year', 4: 'sex'}, inplace=True)

    df.to_csv("processed_dataset/players.csv")
    print(df.head())
    print(split_by_index(rows[0], positions))

def load_ranking():
    df = pd.read_csv("processed_dataset/global.csv")
    df['date'] = pd.to_datetime(df["date"], format='%d/%m/%Y')
    return df.iloc[:,1:]
def load_players():
    df = pd.read_csv("processed_dataset/players.csv")
    return df.iloc[:, 1:]

