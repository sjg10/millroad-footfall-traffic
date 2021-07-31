import requests
import csv
import matplotlib.pyplot as plt
from datetime import datetime

import matplotlib.dates as mdates
import numpy as np

md_url = "https://data.cambridgeshireinsight.org.uk/api/3/action/package_show?id=52aaa64f-0f3d-4130-86cd-f24290378d33"

api_cols_ret =  ['Local Time (Sensor)', 'Date', 'Time', 'countlineName', 'direction', 'Car', 'Pedestrian', 'Cyclist', 'Motorbike', 'Bus', 'OGV1', 'OGV2', 'LGV']
data_cols = ['Car', 'Pedestrian', 'Cyclist', 'Motorbike', 'Bus', 'OGV1', 'OGV2', 'LGV']

months = mdates.MonthLocator()  # every month
weeks = mdates.WeekdayLocator()  # every week
months_fmt = mdates.DateFormatter('%m/%Y')


def get_sensor_map(md_url):
    """ Retrieve a map of sensor to sensor info """
    r = requests.get(md_url)
    res = None
    resource_map = {}
    if r.status_code == 200:
        js = r.json()
        for resource in js["result"][0]["resources"]:
            print("Found sensor ",resource["name"] , "@", resource["revision_timestamp"])
            resource_map[resource["name"]] = resource
    return resource_map

def get_data_as_csv(resource):
    """ Use a sensor info dict entry from get_sensor_map to get data for a sensor"""
    print("Fetching sensor", resource["name"])
    r = requests.get(resource["url"])
    if r.status_code == 200:
        decoded_content = r.content.decode('latin-1')
        return csv.reader(decoded_content.splitlines(), delimiter=',')



def get_lines(sensor_map, sensor, modes):
    data = get_data_as_csv(sensor_map[sensor])
    headers = next(data, None)
    dates = []
    date_collapse_data_in =[]
    date_collapse_data_out =[]
    date_collapse_data_total =[]

    cur_date = None
    cur_date_in = []
    cur_date_out = []
    cur_date_total = []

    idx_date=headers.index("Date")
    idx_dir=headers.index("direction")
    idxs_data=[headers.index(x) for x in modes]
    data_cols = len(idxs_data)

    def week(date): return int(date.strftime("%W")) # Get week of year starting on Monday

    for row in data:
        rowdate =  datetime.strptime(row[idx_date], "%d/%m/%Y")
        if cur_date and week(cur_date) != week(rowdate):
            #print("Averaging data on ",cur_date, week(cur_date))
            dates.append(np.datetime64(cur_date))
            date_collapse_data_in.append([x for x in cur_date_in])
            date_collapse_data_out.append([x for x in cur_date_out])
            date_collapse_data_total.append([x for x in cur_date_total])
        if not cur_date or week(cur_date) != week(rowdate):
            cur_date_in = [0 for x in range(data_cols)]
            cur_date_out = [0 for x in range(data_cols)]
            cur_date_total = [0 for x in range(data_cols)]
            cur_date = rowdate
        if row[idx_dir] == "in":
            for i,idx in enumerate(idxs_data):
                cur_date_in[i] += int(row[idx])
                cur_date_total[i] += int(row[idx])
        elif row[idx_dir] == "out":
            for i,idx in enumerate(idxs_data):
                cur_date_out[i] += int(row[idx])
                cur_date_total[i] += int(row[idx])
        else: raise ValueError()
    print("Retrieved range", dates[0], dates[-1])
    return dates, date_collapse_data_in, date_collapse_data_out, date_collapse_data_total


def add_keydates(ax):
    """ add keydates to a plot """
    bridge_closed_2019 = np.datetime64("2019-07-01")
    bridge_open_2019 = np.datetime64("2019-09-01")
    bridge_closed_2020 = np.datetime64("2020-06-23")

    important_dates = [
            (np.datetime64("2020-03-23"), "1st Lockdown"),
            (np.datetime64("2020-10-13"), "2nd Lockdown"),
            (np.datetime64("2021-01-06"), "3rd Lockdown"),
            (np.datetime64("2021-04-12"), "S2 Easing")
            #(np.datetime64("2021-05-17"), "S3 Easing"),
            #(np.datetime64("2021-06-21"), "S4 Easing")
            ]

    ymax= plt.ylim()[1]

    ax.axvspan(bridge_closed_2019, bridge_open_2019, alpha=0.5, color='dimgray', label="Bridge Closed 2019")
    plt.text(bridge_closed_2019, ymax, "Bridge Closed '19")
    ax.axvspan(bridge_closed_2020, np.datetime64(mdates.num2date(plt.xlim()[1])), alpha=0.5, color='dimgray', label="Bridge Closed 2020")
    plt.text(bridge_closed_2020, ymax, "Bridge Closed '20")

    markers = []
    for date,name in important_dates:
        markers.append(plt.axvline(x=date))
        plt.text(date, ymax, name)
        markers[-1].set_linestyle("-")
        markers[-1].set_color("dimgray")

def get_loc_map():
    """Ripped from  Mill Road Trial: Sensor point locations so we dont have to decode xlsx"""
    loc_map = {}
    loc_map["Sensor 1: Mill Road"] = "362 Mill Rd"
    loc_map["Sensor 2: Mill Road"] = "Mill Rd (SO 1 Mortimer Rd)"
    loc_map["Sensor 3: Coleridge Road"] = "108 Coleridge Rd"
    loc_map["Sensor 4: Vinery Road"] = "114 Vinery Rd"
    loc_map["Sensor 41: Tenison Road"] = "2 Tenison Rd"
    loc_map["Sensor 6: Station Road"] = "OP 6 Station Rd"
    loc_map["Sensor 7: Coldhams Lane"] = "151/153 Coldhams Ln"
    loc_map["Sensor 40: Cherry Hinton Road"] = "117 Cherry Hinton Rd"
    loc_map["Sensor 16: Perne Road"] = "142 Perne Road"
    loc_map["Sensor 10: East Road"] = "O/S ARU East Road"
    loc_map["Sensor 12: Devonshire Road Cycle Path"] = "55 Devonshire Rd"
    loc_map["Sensor 13: Milton Road"] = "214 Milton Rd"
    loc_map["Sensor 14: Hills Road"] = "140 Hills Rd"
    loc_map["Sensor 15: Newmarket Road"] = "560 Newmarket Road"
    return loc_map

def plot_sensor(ax, sensor_map, sensor, modes, plot_in, plot_out, plot_total):
    lines = get_lines(sensor_map, sensor, modes)
    if plot_in:    ax.plot(lines[0], [x[0] for x in lines[1]], label=get_loc_map()[sensor] + " (in)")
    if plot_out:   ax.plot(lines[0], [x[0] for x in lines[2]], label=get_loc_map()[sensor] + " (out)")
    if plot_total: ax.plot(lines[0], [x[0] for x in lines[3]], label=get_loc_map()[sensor] + " (total)")
    ax.legend()

def setup_plot(fig, ax, modes):    
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(months_fmt)
    ax.xaxis.set_minor_locator(weeks)

    add_keydates(ax)

    ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.grid(True)

    fig.autofmt_xdate()
    plt.xticks(rotation=90)
    plt.ylim(bottom=0)
    plt.xlabel("Date",fontdict = {'fontsize': 14})
    plt.ylabel("Counts",fontdict = {'fontsize': 14})
    plt.title("Traffic Counts Cambridge (Sum of " + str(modes) + ")", pad = 30, fontdict = {'fontsize': 18})


if __name__ == "__main__":
    sensor_map = get_sensor_map(md_url)
    fig, ax = plt.subplots()
    #modes = ["Pedestrian", "Cyclist"]
    modes = ["Car", "Motorbike", "OGV1", "OGV2", "LGV"] # all vehicle types excluding bus
    plot_sensor(ax, sensor_map, "Sensor 1: Mill Road", modes, False, False, True)
    plot_sensor(ax, sensor_map, "Sensor 2: Mill Road", modes, False, False, True)
    plot_sensor(ax, sensor_map, "Sensor 7: Coldhams Lane", modes, False, False, True)
    setup_plot(fig, ax, modes)

    plt.show()
