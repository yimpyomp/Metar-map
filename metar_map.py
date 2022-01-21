# Import statements
import plotly.express as px
import pandas as pd
import avwx
import requests
from bs4 import BeautifulSoup
import json

# JSON database replaced coordinate scraper
# Coordinate scraper function replaced geopy
# from geopy.geocoders import Nominatim
# geolocator = Nominatim(user_agent="GoogleV3")

# Make a list containing ICAO identifiers for desired airports, dictionary containing color key
# airport_list = ['KDWH', 'KCLL', 'KIAH', 'KTME', 'KHOU', 'KEFD', 'KGLS', 'KTYR', 'KACT', 'KELP']
color_key = {'VFR': 'green', 'MVFR': 'blue', 'IFR': 'red', 'LIFR': 'fuchsia'}
airport_list = ['KAMA', 'KELP', 'KLBB', 'KMAF', 'KABI', 'KSJT', 'KDRT', 'KDFW', 'KSAT', 'KIAH', 'KHOU', 'KDWH']


# Using web scraping function to generate list of airports
def get_airports():
    # Creating URL object
    url = 'https://airportcodes.io/en/country/united-states/'
    # Creating object page
    page = requests.get(url)
    # Using beautiful soup to get data
    soup = BeautifulSoup(page.text, 'lxml')
    table1 = soup.find('table')
    # Creating a column list
    headers = []
    for i in table1.find_all('th'):
        title = i.text
        headers.append(title)
    # Convert to pandas data frame
    airport_codes = pd.DataFrame(columns=headers)
    # Filling dataframe using for loop
    for j in table1.find_all('tr')[1:]:
        row_data = j.find_all('td')
        row = [i.text for i in row_data]
        length = len(airport_codes)
        airport_codes.loc[length] = row
    # Removing unnecessary columns
    airport_codes = airport_codes.drop(['IATA', 'FAA', 'Name', 'Type', 'Municipality'], axis=1)
    # Converting to list
    identifier_list = airport_codes['ICAO'].tolist()
    # Printing status
    print('Airport list complete')
    # Returning list
    return identifier_list


def coordinate_scraper(airports):
    """
    Scrapes AirNav for airport coordinates
    :param airports: List of ICAO identifiers
    :return: List containing airport latitudes and longitudes
    """
    # Creating empty lists to store longitude and latitude values
    latitudes = []
    longitudes = []
    # Assigning url to variable
    url = 'https://www.airnav.com/airport/'
    # Iterating through list of airports
    for airport in airports:
        # Getting data with requests
        airport_page = requests.get(url + airport)
        # Parsing with beautiful soup
        soup = BeautifulSoup(airport_page.text, 'html.parser')
        # Working through the nested tables
        tables = soup.find_all('table')
        subs = tables[6].find_all('table')
        target = subs[0]
        # String containing raw coordinate data
        raw_coords = target.find_all('td')
        # Last set with estimated text
        split_coordinates = (raw_coords[3].text).split('W')
        estimated_coordinates = split_coordinates[2].split(',')
        # Adding latitude to list
        latitudes.append(estimated_coordinates[0])
        # Taking longitude and adding to list
        raw_longitude = estimated_coordinates[1].split('(')
        longitudes.append(raw_longitude[0])
    # Returning lists
    return latitudes, longitudes


# Function to pull latitude and longitude data from a JSON database
def json_coordinates(airports):
    # Assigning URL to variable
    url = 'https://raw.githubusercontent.com/mwgg/Airports/master/airports.json'
    # Accessing with requests and loading into a python object
    resp = requests.get(url)
    airport_data = resp.json()
    # Creating empty lists for coordinates
    latitudes = []
    longitudes = []
    # Iterating through airports
    for airport in airports:
        latitudes.append(airport_data[airport]['lat'])
        longitudes.append(airport_data[airport]['lon'])
    return latitudes, longitudes


def get_flight_rules(airports, color_key):
    # Creating empty list to store flight rule values
    current_rules = []
    # Empty list to store colors corresponding to current rules
    color_codes = []
    # Iterating through list of airports
    for airport in airports:
        # Creating a METAR object and fetching current data
        current_report = avwx.Metar(airport)
        current_report.update()
        # Adding current flight rules to list
        current_rules.append(current_report.data.flight_rules)
        # Storing rule in variable for color list
        current_field_condition = current_report.data.flight_rules
        # Populating empty color list based on current rules
        color_codes.append(color_key[current_field_condition])
    print('Flight rules complete')
    # Returning list of flight rules
    return current_rules, color_codes


# Based on nesting of functions coordinate method is unreachable, removing option for web scraper
def dataframe_converter(airports, current_rules, color_codes):
    # Retrieving airport coordinates using JSON database
    latitudes, longitudes = json_coordinates(airports)
    # Converting lists to a pandas dataframe
    df = pd.DataFrame(list(zip(latitudes, longitudes)), columns=['Latitude', 'Longitude'])
    # Adding column with airport identifiers
    df['Identifier'] = pd.Series(airports)
    # Adding flight conditions and color code to dataframe
    df['Rules'] = pd.Series(current_rules)
    df['Color'] = pd.Series(color_codes)
    df['Color'] = df['Color'].astype(str)
    print('Data frame conversion complete: ')
    # Returning dataframe
    print(df)
    return df


def metar_mapper(airports, color_key):
    # Using function to get current flight conditions and corresponding color code
    current_flight_rules, current_colors = get_flight_rules(airports, color_key)
    # Creating dataframe
    metar_df = dataframe_converter(airports, current_flight_rules, current_colors)
    # Plotting results
    print('Displaying map')
    metar_map = px.scatter_geo(metar_df, lat='Latitude', lon='Longitude', color='Rules', color_discrete_map=color_key,
                               hover_name='Identifier')
    metar_map.update_geos(scope='usa')
    metar_map.show()


airports = get_airports()
metar_mapper(airports, color_key)
#metar_mapper(airport_list, color_key)

