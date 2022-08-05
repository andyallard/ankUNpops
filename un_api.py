import requests
import json
import datetime
import pandas as pd
from pathlib import Path


# the UN's API includes many entities which are not sovereign states,
# yet are listed as "Country". This workaround is a manuel fix for if
# one is only interested in countries by the classic definition
not_countries = [
    'American Samoa',
    'Bermuda',
    'British Virgin Islands',
    'Cayman Islands',
    'Mayotte',
    'Cook Islands',
    'Faroe Islands',
    'Falkland Islands (Malvinas)',
    'French Guiana',
    'French Polynesia',
    'Gibraltar',
    'Greenland',
    'Guadeloupe',
    'Guam',
    'China, Hong Kong SAR',
    'China, Macao SAR',
    'Martinique',
    'Montserrat',
    'Curaçao',
    'Aruba',
    'Sint Maarten (Dutch part)',
    'Bonaire, Sint Eustatius and Saba',
    'New Caledonia',
    'Niue',
    'Northern Mariana Islands',
    'Puerto Rico',
    'Réunion',
    'Saint Helena',
    'Anguilla',
    'Saint Pierre and Miquelon',
    'Tokelau',
    'Turks and Caicos Islands',
    'Isle of Man',
    'United States Virgin Islands',
    'Wallis and Futuna Islands',
]


# Much of the code, including this function were adapted from the following
# address: https://population.un.org/dataportal/about/dataapi
def callAPI(relative_path: str, topic_list: bool = False) -> pd.DataFrame:
    base_url = "https://population.un.org/dataportalapi/api/v1"
    target = base_url + relative_path
    # Calls the API
    response = requests.get(target)
    # Reformats response into a JSON object
    j = response.json()
    # The block below will deal with paginated results.
    # If results not paginated, this will be skipped.
    try:
        # If results are paginated, they are transformed into a
        # python dictionary.
        # The data may be accessed using the 'data' key of the dictionary.
        df = pd.json_normalize(j['data'])
        # As long as the nextPage key of the dictionary contains an
        # address for the next API call, the function will continue
        # to call the API and append the results to the dataframe.
        count = 1
        while j['nextPage'] is not None:
            response = requests.get(j['nextPage'])
            j = response.json()
            df_temp = pd.json_normalize(j['data'])
            df = pd.concat([df, df_temp])
            count += 1
            print(f'Multiple pages returned by API. This might take'
                  f' some time... page {count}', end='\r')
    except Exception:
        if topic_list:
            df = pd.json_normalize(j, 'indicators')
        else:
            df = pd.DataFrame(j)
    return(df)


def callAPI_and_print(relative_path):
    """
    This function is meant for development purposes, to visualize the
    data that is coming back from the API. Once a person knows exactly what
    calls to make, only the function callAPI should be used.
    """
    df_returned = callAPI(relative_path)
    print_heading(relative_path)
    print(df_returned)
    return df_returned


def print_heading(heading_string):
    print('\n' + '-'*25 + heading_string + '-'*25)


def create_relative_path(indicators, locations, startYear=-1, endYear=-1):
    if startYear == -1:
        startYear = current_year()
    if endYear == -1:
        endYear = current_year()

    chaine = f'/data/indicators/{indicators}/locations/{locations}/' \
             f'start/{startYear}/end/{endYear}'
    return chaine


def current_year():
    current_date_and_time = datetime.datetime.now()
    current_date = current_date_and_time.date()
    year = current_date.year
    return year


def write_to_file_json(user_data):
    filepath = Path(__file__).parent / "data"
    filepath.mkdir(exist_ok=True)
    filename = str(filepath) + f'\\countries.json'
    with open(filename, 'w') as fn:
        fn.write(json.dumps(user_data, sort_keys=True, indent=4))


def converter(object):
    """ This function converts objects into strings so that they
     can be serialized in JSON"""
    # if isinstance(object, datetime.datetime):
    #     return object.__str__()
    return object.__str__()


def country_populations_current_year() -> pd.DataFrame:
    # These options change the visual display of pandas.DataFrame objects
    # Useful for adapting/debugging
    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.max_rows', None)

    # THE FOLLOWING LINES ARE USEFUL FOR ADAPTING THIS PROGRAM TO EXTRACT
    # OTHER TYPES OF DATA
    # topics = callAPI_and_print('/topics/')
    # df_locations = callAPI_and_print('/locations/')
    # pop_indicators = callAPI_and_print('/topics/Pop/indicators/')
    df_locations = callAPI('/locations/')

    # the API call returns information for all locations, but we want to
    # extract only the countries (not continents or autonomous regions)
    countries = df_locations[df_locations['locationType'] == "Country"]
    # see link for use of '~'
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#boolean-indexing
    countries = countries[~countries['name'].isin(not_countries)]
    # Stores country codes in a list
    country_codes = [str(code) for code in countries["id"].values]
    # Converts country code list into a string to be used in  API call
    country_selection_string = ",".join(country_codes)
    relative_path = create_relative_path(49, country_selection_string)
    population = callAPI(relative_path)

    # This is an alternative call with only 9 countries, useful for testing
    # relative_path = create_relative_path(49, '4,8,12,20,24,28,31,32,36')
    # population = callAPI(relative_path)

    # filters the returned results
    population = population.loc[(population['variant'] == "Median") &
                                (population['sex'] == "Both sexes"),
                                ['location', "indicator", "variant", "value"]
                                ]

    population.reset_index(drop=True, inplace=True)

    write_to_file_json(population.to_json())
    return population


if __name__ == '__main__':
    population = country_populations_current_year()
    print_heading('Countries')
    print(population)
