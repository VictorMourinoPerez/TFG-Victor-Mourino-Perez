import sqlite3
import csv as csv
from geographiclib.geodesic import Geodesic
from geographiclib.constants import Constants as constant
from time import time
from datetime import datetime
from datetime import timedelta
import math
from kmlGen import *
import os.path
import os
from scraper import *
from metar import Metar
import random
import pickle

original_path = 'test'
xtension = '.csv'

def dms2dd(tranX):
    # Convert the string coordinates (DDºMM'SS'') into float decimal degree
    degrees = 0
    minutes = 0
    seconds = 0
    new_tranX = []
    for x in tranX:
        new_tranX.append([])
        degrees = float(x[0][0:2])
        minutes = float(x[0][3:5])
        seconds = float(x[0][6:10])
        new_tranX[-1].append(degrees + minutes / 60 + seconds / 3600)
        degrees = float(x[0][13:16])
        minutes = float(x[0][17:19])
        seconds = float(x[0][20:24])
        new_tranX[-1].append(degrees + minutes / 60 + seconds / 3600)
    return new_tranX


european_airlines = ["VLG", "RYR", "EZY", "IBE", "DLH", "IBK", "AEA", "WZZ", "TAP", "BAW", "AFR", "AZA", "KLM", "SWR", "BCS", "BEL", "EZS", "EXS", "GWI", "EWG", "UPS", "MAC", "DAH", "FIN", "TVF", "RAM", "AEE", "EIN", "TRA", "AUI", "EVE", "TVS", "BTI", "BER", "ROT", "NLY",  "ATL", "MLD", "ANE", "ASL", "FLI", "AUA", "UTN", "BRU", "BLA", "LZB", "CIB", "CTN", "CSA", "MSR", "ENT", "GES", "GJT", "JON", "LDM", "LVL", "LOT", "LGL", "SAS", "SQP", "LLC", "TUI", "TAR", "WRC", "WZZ", "NJE"]
american_airlines = ["AAL", "DAL", "NAX", "ROU", "TSC", "UAL", "WJA"]
latam_airlines = ["AVA", "ARG", "TAM", "AMX"]
other_airlines = ["KTK", "QTR", "AFL", "UAE", "ELY", "TAY", "SIA", "PGT", "RJA", "THY", "CCA", "SNG", "AIZ", "AAR", "AHY", "AZV", "CPA", "ETD", "TGZ", "RSY", "ISR", "KLA", "LAN", "IRM", "PIA", "KAR", "SDM", "ABG", "SBI", "SIA", "SVR"]

start_time = time()
ARP_LEBL = [41.29694444, 2.07833333]
touch_zones = [["41°18'14.0”N 002°05'54.3”E"],  # 25R
               ["41°17'26.3”N 002°05'55.3”E"],  # 25L
               ["41°17'47.4”N 002°04'36.5”E"],  # 07L
               ["41°17'02.0”N 002°04'44.3”E"],  # 07R
               ["41°17'28.9”N 002°05'11.3”E"]]  # 02
touch_zones = dms2dd(touch_zones)
touch_zones_names = ["25R", "25L", "07L", "07R", "02"]
airlines = [""]
metar_times = []
delta_time = 600.00  # seconds between different actual flights

class Instance:
    def __init__(self):
        self.identifier = None
        self.callsign = None
        self.initial_time = None
        self.final_time = None
        self.coordinates = None
        self.headings = None
        self.altitudes = None
        self.ias = None
        self.baro = None
        self.winddirection = None
        self.windspeed = None
        self.gs = None
        self.tas = None
        self.rwy = None
        self.iaf_time = None
        self.initial_density = None
        self.typecode = None
        self.wtc = None
        self.mixindex = None
        self.ttl = None
        self.ARPdist = None
        self.ARPazi = None
        self.Dayoftheweek = None
        self.Company = None
        self.Altitude = None
        self.Heading = None
        self.Ias = None
        self.Gs = None
        self.InitialTime = None
        self.Baro = None
        self.Wind_direction = None
        self.Wind_vrb = None
        self.Wind_speed = None
        self.Visibility = None
        self.InitialTime_68 = None
        self.CRC = 0

data = []
instances = []
raw_id = []
raw_coordinates = []
raw_headings = []
raw_altitudes = []
raw_ias = []
raw_tas = []
raw_gs = []
raw_baro = []
raw_windspeed = []
raw_winddirection = []
pms_icao = []
pms_category = []
pms_callsign = []





def saveVariable(obj, name):
    with open(name+'.pkl', 'wb') as f:
        pickle.dump(obj, f)


def loadVariable(name):
    with open(name+'.pkl', 'rb') as f:
        obj0 = pickle.load(f)
        return obj0


def twoPointsDistance(point1, point2):
    # Returns the distance in meters between two points expressed as follows:
    # point = [lat, lon] where type(lat,lon) = double
    lat1 = point1[0]
    lon1 = point1[1]
    lat2 = point2[0]
    lon2 = point2[1]
    distance = Geodesic.Inverse(Geodesic(constant.WGS84_a, constant.WGS84_f), lat1, lon1, lat2,
                                lon2).__getitem__('s12')
    return distance


def twoPointsAzimut(point1, point2):
    # Returns the azimut between two points expressed as follows:
    # point = [lat, lon] where type(lat,lon) = float
    lat1 = point1[0]
    lon1 = point1[1]
    lat2 = point2[0]
    lon2 = point2[1]
    azimut = Geodesic.Inverse(Geodesic(constant.WGS84_a, constant.WGS84_f), lat1, lon1, lat2,
                                lon2).__getitem__('azi1')
    if azimut < 0:
        azimut += 360
    return azimut


def data2instances():
    global instances, delta_time, data
    with open(original_path+xtension) as csv_file:
        reader = csv.reader(csv_file, delimiter=';')
        data = list(reader)
    # Try to extract each flight's flight segments
    csv_line = 0
    # len(set_data) - 8 because each aircraft has 8 lines als (<=)
    while csv_line <= len(data) - 8:
        initial_length = len(instances)
        temp_coordinates = data[csv_line + 2]
        nested_coordinates = []
        counter = 0
        while counter <= len(temp_coordinates) - 4:
            # counter: latitude {float}
            # counter + 1: longitude {float}
            # counter + 2: altitude {float} [m]
            # counter + 3: timestamp {datetime}
            nested_coordinates.append([float(temp_coordinates[counter].replace(",", ".")), float(temp_coordinates[counter + 1].replace(",", ".")), int(temp_coordinates[counter + 2]) * 0.3048, datetime.strptime(temp_coordinates[counter + 3], "%d/%m/%Y %H:%M:%S")])
            counter += 4
        airborne_indexes = [j for j in range(len(nested_coordinates) - 1) if (nested_coordinates[j+1][3] - nested_coordinates[j][3]).total_seconds() >= delta_time]

        airborne_indexes.insert(0, 0)
        airborne_indexes.append(len(nested_coordinates) - 1)
        arrival_indexes = [[airborne_indexes[i], airborne_indexes[i + 1]] for i in range(len(airborne_indexes) - 1) if nested_coordinates[airborne_indexes[i]][2] >= 350 and nested_coordinates[airborne_indexes[i+1]][2] <= 25]
        # Creating each instance from its coordinates and altitudes
        for interval in arrival_indexes:
            if interval[0] != 0:
                index_1 = interval[0] + 1
            else:
                index_1 = interval[0]
            index_2 = interval[1]
            instances.append(Instance())
            instances[-1].callsign = data[csv_line][0]
            instances[-1].identifier = data[csv_line][1]
            temp_list_coordinates = []
            temp_list_altitudes = []
            for i in range(index_1+1, index_2):
                if twoPointsDistance(nested_coordinates[i - 1][0:2], nested_coordinates[i][0:2]) <= 30000:
                    # Append the coordinates+its timestamp
                    temp_list_coordinates.append(nested_coordinates[i][0:2])
                    temp_list_coordinates[-1].append(nested_coordinates[i][3])
                    # Append the altitude and its timestamp
                    temp_list_altitudes.append([nested_coordinates[i][2]])
                    temp_list_altitudes[-1].append(nested_coordinates[i][3])
            instances[-1].coordinates = temp_list_coordinates
            instances[-1].altitudes = temp_list_altitudes
            # Initial & final time
            try:
                instances[-1].initial_time = temp_list_coordinates[0][2]
                instances[-1].final_time = temp_list_coordinates[-1][2]
            except:
                instances[-1].initial_time = datetime.now()
                instances[-1].final_time = datetime.now()
                instances[-1].CRC = 1
        final_length = len(instances)
        # Adding other features
        # IAS --> csv_line + 4
        # GS --> csv_line + 7
        temp_ias = data[csv_line + 4]
        nested_ias = []
        if len(temp_ias) >= 2:
            counter = 0
            while counter <= len(temp_ias) - 2:
                # counter: ias {int}
                # counter + 1: timestamp {datetime}
                nested_ias.append([int(temp_ias[counter]), datetime.strptime(temp_ias[counter + 1], "%d/%m/%Y %H:%M:%S")])
                counter += 2
        temp_gs = data[csv_line + 7]
        nested_gs = []
        if len(temp_gs) >= 3:
            counter = 0
            while counter <= len(temp_gs) - 3:
                # counter: gs {float}
                # counter + 1: TAS (not used)
                # counter + 2: timestamp {datetime}
                nested_gs.append([float(temp_gs[counter].replace(",", ".")), datetime.strptime(temp_gs[counter + 2], "%d/%m/%Y %H:%M:%S")])
                counter += 3
        for i in range(initial_length, final_length):
            t = instances[i].initial_time
            if len(nested_ias) == 0:
                instances[i].Ias = 250
            else:
                for j in range(len(nested_ias)):
                    if t - timedelta(0, 1200) <= nested_ias[j][1] <= t + timedelta(0, 1200):
                        instances[i].Ias = nested_ias[j][0]
                        break
                if instances[i].Ias == None:
                    instances[i].Ias = 250
            if len(nested_gs) == 0:
                instances[i].Gs = instances[i].Ias
            else:
                for j in range(len(nested_gs)):
                    if t - timedelta(0, 1200) <= nested_gs[j][1] <= t + timedelta(0, 1200):
                        instances[i].Gs = nested_gs[j][0]
                        break
                if instances[i].Gs == None:
                    instances[i].Gs = instances[i].Ias
        csv_line += 8


def extract_RWY():
    global instances
    counter_1 = 0
    while counter_1 < len(instances):
        try:
            lat_1 = instances[counter_1].coordinates[-4][0]  # penultimate position latitude
            lon_1 = instances[counter_1].coordinates[-4][1]  # penultimate position longitude
            lat_2 = instances[counter_1].coordinates[-1][0]  # last position latitude
            lon_2 = instances[counter_1].coordinates[-1][1]  # last position longitude

            azi1 = twoPointsAzimut([lat_1, lon_1], [lat_2, lon_2])

            if 225 < azi1 < 265:  # RWY 25L/R: 245º
                lat_1 = touch_zones[0][0]  # [25R][latitude]
                lon_1 = touch_zones[0][1]  # [25R][longitude]
                distance_25R = Geodesic.Inverse(Geodesic(constant.WGS84_a, constant.WGS84_f), lat_1, lon_1, lat_2,
                                                lon_2).__getitem__('s12')
                lat_1 = touch_zones[1][0]  # [25L][latitude]
                lon_1 = touch_zones[1][1]  # [25L][longitude]
                distance_25L = Geodesic.Inverse(Geodesic(constant.WGS84_a, constant.WGS84_f), lat_1, lon_1, lat_2,
                                                lon_2).__getitem__('s12')
                if distance_25R < distance_25L:
                    instances[counter_1].rwy = touch_zones_names[0]  # set RWY 25R
                else:
                    instances[counter_1].rwy = touch_zones_names[1]  # set RWY 25L
            elif 45 < azi1 < 85:  # RWY 07L/R: 65º
                lat_1 = touch_zones[2][0]  # [07L][latitude]
                lon_1 = touch_zones[2][1]  # [07L][longitude]
                distance_07L = Geodesic.Inverse(Geodesic(constant.WGS84_a, constant.WGS84_f), lat_1, lon_1, lat_2,
                                                lon_2).__getitem__('s12')
                lat_1 = touch_zones[3][0]  # [07R][latitude]
                lon_1 = touch_zones[3][1]  # [07R][longitude]
                distance_07R = Geodesic.Inverse(Geodesic(constant.WGS84_a, constant.WGS84_f), lat_1, lon_1, lat_2,
                                                lon_2).__getitem__('s12')
                if distance_07L < distance_07R:
                    instances[counter_1].rwy = touch_zones_names[2]  # set RWY 07L
                else:
                    instances[counter_1].rwy = touch_zones_names[3]  # set RWY 07R
            elif 8 < azi1 < 38:  # RWY 02: 18º
                instances[counter_1].rwy = touch_zones_names[4]  # set RWY 02
        except:
            print(" 313 - Trouble in index ", counter_1, " ", instances[counter_1].identifier)
            instances[counter_1].CRC = 1
        counter_1 += 1


def features():
    global instances
    for flight in instances:
        # The first heading of each aircraft
        try:
            point_1 = flight.coordinates[0][0:2]
            point_2 = flight.coordinates[1][0:2]
            flight.Heading = twoPointsAzimut(point_1, point_2)
        except:
            print("line 329")
        # The concentric circles' constraint
        # Coordinates are inverted so the scan is done from the airports towards outside--> less time consuming
        # The radius is set to 68 km because it contains the holdings
        max_distance = twoPointsDistance(flight.coordinates[0][0:2], ARP_LEBL)
        min_distance = twoPointsDistance(flight.coordinates[-1][0:2], ARP_LEBL)
        if max_distance < 68000 or min_distance > 68000:
            # If the maximum distance of the flight with respect to the ARP of LEBL is less than the inner circle, it is excluded from the flight pool
            flight.CRC = 1
        else:
            # For those flights which have positions further than 68 km it is necessary to delete those positions.
            delete_index = 0
            for coordinate in flight.coordinates:
                if twoPointsDistance(coordinate[0:2], ARP_LEBL) <= 68000:
                    delete_index = flight.coordinates.index(coordinate)
                    flight.coordinates = flight.coordinates[delete_index:-1]
                    flight.altitudes = flight.altitudes[delete_index:-1]
                    flight.ttl = flight.coordinates[-1][2] - flight.coordinates[0][2]
                    break
        # Add company
        if len(flight.callsign) < 8 or flight.callsign[0] == "#" or flight.callsign[0] == "_":
            path = os.getcwd()
            termination = "\\Logs"
            path = path+termination
            file_folder = flight.identifier
            file_name = "_CALLSIGN.dat"
            separator = "\\"
            try:
                with open(separator.join([path, file_folder, file_name]), 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if len(line.split("\t")[7].split("\n")[0]) == 8 and line.split("\t")[7].split("\n")[0][0] != "#" and line.split("\t")[7].split("\n")[0][0] != "_" and line.split("\t")[7].split("\n")[0] != "CALLSIGN":
                            flight.callsign = line.split("\t")[7].split("\n")[0]
                            flight.Company = line.split("\t")[7].split("\n")[0][0:3]
                            break
                    if len(flight.callsign) == 0:
                        # aircraft_company is a list of [icao, company] of flights which file _CALLSIGN.dat is empty
                        aircraft_company = loadVariable("aircraft_company")
                        for x in aircraft_company:
                            if flight.identifier == x[0]:
                                flight.Company = x[1]
                                flight.callsign = x[1]
                        if len(flight.callsign) == 0:
                            print(flight.identifier," is not in aircraft_company.pkl")
                            flight.CRC = 1
            except:
                print(flight.identifier," ", flight.callsign)
                flight.CRC = 1
        else:
            flight.Company = flight.callsign[0:3]


def assign_category():
    global instances, metar_times
    blacklist = []

    # Connection with the database (icao24, model, typecode)
    con = sqlite3.connect('aircraftDB.db')
    cur = con.cursor()
    counter = 1

    for flight in instances:
        if not metar_times.__contains__(flight.initial_time):
            metar_times.append(flight.initial_time)
        icao = flight.identifier[2::]
        query = "SELECT typecode FROM aircraftTable WHERE icao24 = \'"+icao+"\'"
        type_code = cur.execute(query)
        type_codes = type_code.fetchall()
        if len(type_codes) == 0:
            if not blacklist.__contains__(icao):
                blacklist.append(icao)
        else:
            flight.typecode = type_codes[0][0]
        counter += 1
    newIcaoType = scrapTypeCode(blacklist)
    query = "INSERT INTO aircraftTable(icao24, model, typecode) VALUES(?,?,?)"
    for x in newIcaoType:
        indexes = [i for i in range(len(instances)) if instances[i].identifier[2::] == x[0]]
        for y in indexes:
            try:
                instances[y].typecode = newIcaoType[newIcaoType.index(x)][2]
            except:
                print(blacklist)
        cur.execute(query,(newIcaoType[newIcaoType.index(x)][0], newIcaoType[newIcaoType.index(x)][1], newIcaoType[newIcaoType.index(x)][2]))
        con.commit()
    con.close()


    def assign_metars(init_time, end_time):
        # This function extracts the desired metars within the time period given by the current flights
        index = 0
        indexf = 0
        metar_file = open("metars.txt", "r").readlines()
        init_day = format_ints(init_time.day)
        init_month = format_ints(init_time.month)
        init_year = str(init_time.year)
        init_datetime = init_year+init_month+init_day
        end_day = format_ints(end_time.day)
        end_month = format_ints(end_time.month)
        end_year = str(end_time.year)
        end_datetime = end_year+end_month+end_day
        hour = "00"
        hour_prime = "01"
        minute = "00"
        minute_prime = "30"
        hourf = "23"
        hourf_prime = "22"
        init_datetime_1 = init_datetime+hour+minute  # Try 00:00
        init_datetime_2 = init_datetime+hour+minute_prime  # Try 00:30
        init_datetime_3 = init_datetime+hour_prime+minute  # Try 01:00
        init_datetime_4 = init_datetime+hour_prime+minute_prime  # Try 01:30
        end_datetime_1 = end_datetime+hourf+minute_prime  # Try 23:30
        end_datetime_2 = end_datetime+hourf+minute  # Try 23:00
        end_datetime_3 = end_datetime+hourf_prime+minute_prime  # Try 22:30
        end_datetime_4 = end_datetime+hourf_prime+minute  # Try 22:00

        init_datetime_1_bool = False
        init_datetime_2_bool = False
        init_datetime_3_bool = False
        for line in metar_file:
            if line.__contains__(init_datetime_1):
                init_datetime_1_bool = True
                index = metar_file.index(line)
            elif line.__contains__(init_datetime_2) and not init_datetime_1_bool:
                init_datetime_2_bool = True
                index = metar_file.index(line)
            elif line.__contains__(init_datetime_3) and not init_datetime_1_bool and not init_datetime_2_bool:
                init_datetime_3_bool = True
                index = metar_file.index(line)
            elif line.__contains__(init_datetime_4) and not init_datetime_1_bool and not init_datetime_2_bool and not init_datetime_3_bool:
                index = metar_file.index(line)
            elif line.__contains__(end_datetime_1) or line.__contains__(end_datetime_2) or line.__contains__(end_datetime_3) or line.__contains__(end_datetime_4):
                indexf = metar_file.index(line)
        metars_old = metar_file[index:indexf+1]
        metars = [metars_old[i][13:-2] for i in range(len(metars_old))]
        metars_datetime = [metars_old[i][0:12] for i in range(len(metars_old))]
        return metars, metars_datetime

    metars, metars_datetime = assign_metars(metar_times[0], metar_times[-1])
    for (metar,metar_datetime) in zip(metars, metars_datetime):
        metar_original = metar
        while True:
            try:
                year = int(metar_datetime[0:4])
                month = int(metar_datetime[4:6])
                obs = Metar.Metar(metar,month,year)
                break
            except:
                try:
                    metar = metar[:-1]
                except:
                    print("Metar: ", metar_original)
        # Solve the problematic with variable wind directions
        if obs.wind_dir != None and obs.wind_dir_from == None:
            wind_dir = obs.wind_dir.value()
            wind_dir_vrb = 0
        elif obs.wind_dir != None and obs.wind_dir_from != None:
            wind_dir = obs.wind_dir.value()
            phi = math.fabs(obs.wind_dir_from.value() - obs.wind_dir_to.value()) % 360
            if phi > 180:
                phi = 360 - phi
            wind_dir_vrb = phi/2
        elif obs.wind_dir == None and obs.wind_dir_from != None:
            wind_dir = random.randrange(0, 359)
            phi = math.fabs(obs.wind_dir_from.value() - obs.wind_dir_to.value()) % 360
            if phi > 180:
                phi = 360 - phi
            wind_dir_vrb = phi/2
        else:
            wind_dir = random.randrange(0, 359)
            wind_dir_vrb = 180
        wind_speed = obs.wind_speed.value()
        try:
            pressure = obs.press.value()
        except:
            print(metar)
        try:
            visibility = obs.vis.value()
        except:
            print(metar)
        try:
            hour = obs.time.hour
        except:
            print(metar)
        try:
            minute = obs.time.minute
        except:
            print(metar)
        try:
            day = obs._day
        except:
            print(metar)

        for flight in instances:
            if (flight.initial_time.hour == hour and minute <= flight.initial_time.minute < minute + 30) and flight.initial_time.day == day:
                flight.Wind_direction = wind_dir
                flight.Wind_vrb = wind_dir_vrb
                flight.Wind_speed = wind_speed
                flight.Baro = pressure
                flight.Visibility = visibility
    f = open("PART 2 — AIRCRAFT TYPE DESIGNATORS (DECODE).txt", 'r', encoding="utf8")
    lines = f.readlines()
    for flight in instances:
        try:
            flight.wtc = [lines[i].split(' ')[-1][0:-1] for i in range(len(lines)) if lines[i].split(' ')[0] == flight.typecode][0]
        except:
            if len(flight.typecode) == 0:
                print(flight.typecode+"is not in the PART 2 — AIRCRAFT TYPE DESIGNATORS (DECODE)")


def initial_density_mixindex():
    #  Calculates the traffic density at the time each AC is detected and the mix index and company assignation
    global instances
    mix_index = []  # Wake turbulence category of each AC
    for flight in instances:
        flight.Dayoftheweek = flight.initial_time.weekday()
        density = 0
        WTC_flight = []

        counter_1 = 0
        while counter_1 < len(instances):
            x = instances[counter_1]
            if x.identifier == flight.identifier and x.initial_time == flight.initial_time:
                pass
            elif x.initial_time <= flight.initial_time <= x.final_time:
                density += 1
                WTC_flight.append(x.wtc)
            counter_1 += 1
        total_flights = len(WTC_flight)
        if total_flights == 0:
            if flight.wtc == 'L' or flight.wtc == 'M':
                flight.mixindex = 100
            elif flight.wtc == 'H' or flight.wtc == 'J':
                flight.mixindex = 300
        else:
            C = (WTC_flight.count('L') + WTC_flight.count('M'))/total_flights*100
            D = (WTC_flight.count('H') + WTC_flight.count('J'))/total_flights*100
            flight.mixindex = C + 3*D
        flight.initial_density = density





def set_arp_dist():
    global instances
    for flight in instances:
        try:
            lat_1 = flight.coordinates[0][0]  # first position latitude
            lon_1 = flight.coordinates[0][1]  # first position longitude
            lat_2 = ARP_LEBL[0]  # last position latitude
            lon_2 = ARP_LEBL[1]  # last position longitude

            azi1 = Geodesic.Inverse(Geodesic(constant.WGS84_a, constant.WGS84_f), lat_1, lon_1, lat_2,
                                    lon_2).__getitem__('azi1')
            s12 = Geodesic.Inverse(Geodesic(constant.WGS84_a, constant.WGS84_f), lat_1, lon_1, lat_2,
                                    lon_2).__getitem__('s12')
            flight.ARPdist = s12
            if azi1 < 0:
                azi1 = azi1+360
            flight.ARPazi = azi1
            flight.InitialTime = flight.initial_time.hour*3600 + flight.initial_time.minute*60 + flight.initial_time.second
            flight.Altitude = flight.altitudes[0][0]
        except:
            print(flight)
            flight.CRC = 1


def cleanInstances():
    global instances
    for flight in instances:
        if flight.CRC == 1:
            instances.pop(instances.index(flight))


def create_X():
    global instances
    X = []
    # Some features are still strings. Maybe those can be used as category-like objects in the ML.
    for flight in instances:
        X.append([])
        X[-1].append(flight.ttl.seconds)
        X[-1].append(flight.InitialTime)
        X[-1].append(flight.ARPdist)
        X[-1].append(flight.ARPazi)
        X[-1].append(flight.Heading)
        X[-1].append(flight.Altitude)
        X[-1].append(flight.Ias)
        X[-1].append(flight.Gs)
        X[-1].append(flight.Baro)
        X[-1].append(flight.Wind_direction)
        X[-1].append(flight.Wind_vrb)
        X[-1].append(flight.Wind_speed)
        X[-1].append(flight.Visibility)
        if european_airlines.__contains__(flight.Company):
            X[-1].append(1)
        else:
            X[-1].append(0)
        if american_airlines.__contains__(flight.Company):
            X[-1].append(1)
        else:
            X[-1].append(0)
        if latam_airlines.__contains__(flight.Company):
            X[-1].append(1)
        else:
            X[-1].append(0)
        if other_airlines.__contains__(flight.Company):
            X[-1].append(1)
        else:
            X[-1].append(0)
        if not european_airlines.__contains__(flight.Company) and not american_airlines.__contains__(flight.Company) and not latam_airlines.__contains__(flight.Company) and not other_airlines.__contains__(flight.Company):
            print(flight.identifier, " - ", instances.index(flight))

        X[-1].append(flight.Dayoftheweek)  # [0:Mon.; 1:Tue.; 2:Wed.; 3:Thu.; 4:Fri.; 5:Sat.; 6:Sun.]
        X[-1].append(flight.mixindex)
        X[-1].append(flight.wtc)  # Str
        X[-1].append(flight.rwy)  # Str
    return X


def create_csv(x):
    instance_header = ["Time_to_land", "Initial_time", "ARP_distance", "ARP_azimuth", "Heading", "Altitude", "IAS", "GS", "Barometric_pressure", "Wind_direction", "Wind_variability", "Wind_speed", "Visibility", "European_airlines", "American_airlines", "Latam_airlines", "Other_airlines", "Day_of_the_week", "Mix_index", "WTC", "RWY"]
    csv_path = "first-test-model_" + original_path+xtension
    with open(csv_path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(instance_header)
        writer.writerows(x)
        print("File created successfully: ", csv_path," from file ", original_path+xtension)
        return

if not os.path.isfile('instances_'+original_path+'.pkl'):
    inittime = time()
    data2instances()
    cleanInstances()
    endtime = time()
    print("data2instances: ", endtime-inittime)
    inittime = time()
    extract_RWY()
    cleanInstances()
    saveVariable(instances, "instances_"+original_path)
    endtime = time()
    print("extract_RWY: ", endtime-inittime)
    inittime = time()
    instances = loadVariable("instances_"+original_path)
    features()
    cleanInstances()
    saveVariable(instances, "instances_features_"+original_path)
    endtime = time()
    print("add_features: ", endtime-inittime)
    kml_builder(instances, original_path)
    print("the end")
    #  Assign category
    inittime = time()
    instances = loadVariable("instances_features_"+original_path)
    assign_category()
    cleanInstances()
    endtime = time()
    print("assign_category: ", endtime-inittime)
    #  Initial density & mix index
    inittime = time()
    initial_density_mixindex()
    cleanInstances()
    endtime = time()
    print("initial_density_mixindex: ", endtime-inittime)

    #  Set arp distance
    inittime = time()
    set_arp_dist()
    cleanInstances()
    endtime = time()
    print("set_arp_dist: ", endtime-inittime)

    inittime = time()
    X = create_X()
    endtime = time()
    print("create_X: ", endtime-inittime)

    inittime = time()
    create_csv(X)
    endtime = time()
    print("create_csv: ", endtime-inittime)
    saveVariable(instances, "first-test-model_"+original_path)
    print("END")
    exit()
if os.path.isfile('instances_'+original_path+'.pkl') and not os.path.isfile('instances_features_'+original_path+'.pkl'):
    inittime = time()
    instances = loadVariable("instances_"+original_path)
    features()
    cleanInstances()
    saveVariable(instances, "instances_features_"+original_path)
    endtime = time()
    print("add_features: ", endtime-inittime)
    kml_builder(instances, original_path)
    print("the end")
    #  Assign category
    inittime = time()
    instances = loadVariable("instances_features_"+original_path)
    assign_category()
    cleanInstances()
    endtime = time()
    print("assign_category: ", endtime-inittime)
    #  Initial density & mix index
    inittime = time()
    initial_density_mixindex()
    cleanInstances()
    endtime = time()
    print("initial_density_mixindex: ", endtime-inittime)
    #  Set arp distance
    inittime = time()
    set_arp_dist()
    cleanInstances()
    endtime = time()
    print("set_arp_dist: ", endtime-inittime)

    inittime = time()
    X = create_X()
    endtime = time()
    print("create_X: ", endtime-inittime)

    inittime = time()
    create_csv(X)
    endtime = time()
    print("create_csv: ", endtime-inittime)
    saveVariable(instances, "firt-test-model_"+original_path)
    print("END")
    exit()
if os.path.isfile('instances_'+original_path+'.pkl') and os.path.isfile('instances_features_'+original_path+'.pkl'):
    #  Assign category
    inittime = time()
    instances = loadVariable("instances_features_"+original_path)
    assign_category()
    cleanInstances()
    endtime = time()
    print("assign_category: ", endtime-inittime)
    #  Initial density & mix index
    inittime = time()
    initial_density_mixindex()
    cleanInstances()
    endtime = time()
    print("initial_density_mixindex: ", endtime-inittime)
    #  Set arp distance
    inittime = time()
    set_arp_dist()
    cleanInstances()
    endtime = time()
    print("set_arp_dist: ", endtime-inittime)

    inittime = time()
    X = create_X()
    endtime = time()
    print("create_X: ", endtime-inittime)

    inittime = time()
    create_csv(X)
    endtime = time()
    print("create_csv: ", endtime-inittime)
    saveVariable(instances, "first-test-model_"+original_path)
    print("END")
    exit()

end_time = time()
elapsed_time = end_time - start_time
print("Elapsed time: %.10f seconds." % elapsed_time)
