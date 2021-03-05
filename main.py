import urllib.request
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline


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

import pandas as pd
import zipfile


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

def convert2df(month, year):
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

    #plt.hist(df['elo'], bins=20, color='blue', edgecolor='black')
    #plt.show()
    df =df[df.elo>2200]
    df["date"] = date
    print(df.head())
    return df

def download_df(month, year):
    download_file(month, year)
    df = convert2df(month, year)
    return df
from datetime import datetime
from datetime import date


def collect_data():
    all_df = []
    month_list = ["jan", "feb", "mar", "avr", "may", "jun", "jul", "agu", "sep", "oct", "nov", "dec"]
    for year in range(2000, 2022):
        for m, month in enumerate(month_list):

            df = convert2df(month, str(year))
            if not df.empty:
                print(df.shape)
                all_df.append(df)
    hist_df = pd.concat(all_df)
    hist_df.to_csv("dataset/global.csv")

def load_players():
    file_name = "dataset/players_list_foa.txt"
    file = open(file_name, "r")
    rows = file.readlines()
    positions = [[0, 15], [15, 76],[76, 79], [152,158]]
    data_list = []
    for row in rows[1:]:
        data_list.append(split_by_index(row, positions))
    df = pd.DataFrame(data_list)
    df.rename(columns={0: 'id', 1: 'name', 2: 'country', 3: 'birth_year'}, inplace=True)
    df.to_csv("dataset/players.csv")
    print(df.head())
    print(split_by_index(rows[0], positions))
collect_data()
#load_players()
players = pd.read_csv("dataset/players.csv")
players = players.drop(columns=["name"])
players = players.iloc[:,1:]
players["birth_year"] = players["birth_year"].astype(int)

scores = pd.read_csv("dataset/global.csv")
scores = scores.iloc[:,1:]
min_elo = 2200
scores = scores[scores.elo> min_elo]
joined = pd.merge(players, scores, how='inner', on='id')
joined['date'] = pd.to_datetime(joined["date"], format = '%d/%m/%Y')
print("Total players processed: ", scores.id.nunique())
print("Player retained: ", joined.id.nunique())
print("Player retained with age:", joined[joined["birth_year"]!=0].id.nunique())
joined = joined[joined["birth_year"]!=0]




#joined["ave_birth"] = pd.to_datetime("01/06/"+str(joined.birth_year))
#joined["age"] = joined["date"] - joined["ave_birth"]
#unfortunately we have just birth year and no date...
#il primo agosto è una media molto approssimativa del giorno di nascita
joined ["first"] = pd.to_datetime("01/08/2000", format = '%d/%m/%Y')
joined["age"] = joined["date"].dt.year - joined["birth_year"] + (joined["date"] - joined ["first"]).dt.days/365.25 - joined["date"].dt.year + 2000
joined["time"] = (joined["date"] - joined ["first"]).dt.days/365.25
joined["age2"] = joined["time"] - joined["date"].dt.year + 2000

date(date.today().year, 1, 1)

print(joined.head())
time = joined["time"].unique()
date = joined["date"].unique()
#print(best_age.head(10))

#print(best_age.index)
def ave_age():

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10,5))
    best_age = joined.groupby("date").apply(lambda x: x.sort_values('elo', ascending=False).head(10).median())
    ax.scatter(date, best_age["age"], color="b", label="Top 10 players")
    spl = UnivariateSpline(best_age["time"], best_age["age"])
    plt.plot(best_age.index, spl(best_age["time"]), 'b', lw=4)

    best_age2 = joined.groupby("date").apply(lambda x: x.sort_values('elo', ascending=False).head(100).median())
    ax.scatter(best_age2.index, best_age2["age"], color="r", label="Top 100 players")
    spl = UnivariateSpline(best_age["time"], best_age2["age"])
    plt.plot(best_age.index, spl(best_age2["time"]), 'r', lw=4)
    best_age3 = joined.groupby("date").apply(lambda x: x.sort_values('elo', ascending=False).head(1000).median())
    ax.scatter(best_age3.index, best_age3["age"], color="g", label="Top 1000 players")
    spl = UnivariateSpline(best_age["time"], best_age3["age"])
    plt.plot(best_age.index, spl(best_age3["time"]), 'g', lw=4)
    ax.legend(bbox_to_anchor=(0.98, 1), loc='upper left')
    ax.set_xlabel("Year", fontsize=14)
    ax.set_ylabel("Average age", fontsize=14)
    fig.suptitle('Average age of best rated chess players', fontsize=16)
    plt.show()
    fig.savefig('age_ranking.png')

ave_age()