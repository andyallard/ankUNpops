import json
import genanki
import datetime
import un_api
import html
import pandas as pd
from pathlib import Path
from math import log10, floor


class MyNote(genanki.Note):
    '''
    This is a modification to the genanki.Note class which allows the creation
    of stable "guid"s. In this case, we only want the country name to be used
    to generate the hash for the guid (the first field is index 0).
    This is explained here: https://github.com/kerrickstaley/genanki#note-guids
    '''
    @property
    def guid(self):
        return genanki.guid_for(self.fields[0])


def sigfig(x: float, sig: int) -> float:
    if str(x)[0] == '1' and x > 10 ** 8:
        sig += 1
    return round(x, sig - int(floor(log10(abs(x)))) - 1)


def generate_path(name):
    filepath = Path(__file__).parent / "data"
    filename = str(filepath) + f'\\{name}.json'
    return filename


def check_last_modified(name):
    try:
        last_modified = Path(generate_path(name)).stat().st_mtime
        last_modified = datetime.date.fromtimestamp(last_modified)
        return last_modified
    except Exception:
        return "...never!"


def read_from_file(name):
    with open(generate_path(name), 'r') as fn:
        json_object = json.loads(fn.read())
        df = pd.read_json(json_object)
        return df


def generate_note_model():
    return genanki.Model(
        1058090155,
        'Country Populations (UN)',
        fields=[
            {'name': 'Country'},
            {'name': 'Population'},
            {'name': 'Year'},
            {'name': 'ISO Country Code'}
        ],
        templates=[
            {
                'name': 'Population',
                'qfmt': 'What was the population of <span class="green">'
                        '{{Country}}</span> in {{Year}}?',
                'afmt': '{{FrontSide}}<hr id="answer"><div class="red">'
                '{{Population}}</div>',
            }
        ],
        css=html.escape(".card {\n  font-family: Verdana;\n  font-size: 4em;\n"
                        "  text-align: center;\n  color: #DDE0BD;\n"
                        "  background-color: #252627;\n}\n\n"
                        ".small { font-size: 0.5em; }\n"
                        ".blue { color: #7A8FE1; }\n"
                        ".green { color: #32936F; }\n"
                        ".red { color: #A15E49; }")
        )


def print_welcome_message():
    s = ' ' * 4
    p = '#'
    date = check_last_modified('countries')
    print('\n' + p * 95)
    print(s, 'Welcome to the Anki Country Population (ankUNpops) deck'
          ' generator')
    print(s, 'The last time data was pulled from the UN Population Division'
          f' database was {date}.')
    print(s, 'The UN releases their report "World Population Prospects"'
          ' generally every 2 years.')
    print(p * 95)
    print('\nBefore your Anki deck is created, you must choose the data'
          ' source.')


def get_data() -> pd.DataFrame:
    choice = ''
    while choice not in ('1', '2'):
        print('Would you like to :\n'
              '    1. Generate Anki deck with existing data (stored locally)\n'
              '    2. Use data directly from the UN Population Division'
              ' database (this will also update the local copy)'
              )
        choice = input('Type 1 or 2: ').strip()

    if choice == '1':
        data = read_from_file('countries')
    else:
        data = un_api.country_populations_current_year()
    return data


if __name__ == '__main__':
    my_model = generate_note_model()
    print_welcome_message()
    data = get_data()

    print(data)

    anki_deck = genanki.Deck(
        20220804,
        'Country Populations (UN)')

    for idx, row in data.iterrows():
        # convert to 2 significant figures
        pop = sigfig(row['value'], 2)
        # convert to string with spaces separating each '000'
        pop = str("{:,}".format(pop)).replace(",", " ")
        country = row['location']
        iso = str(row['locationId'])
        # print(country, pop)
        n = MyNote(
            model=my_model,
            fields=[country, pop, str(un_api.current_year()), iso]
        )
        # This line is useful for debugging
        # print(idx, n.fields, n.guid)
        anki_deck.add_note(n)

    # create Anki deck
    path = Path(__file__).parent
    genanki.Package(anki_deck).write_to_file(path / 'ankUNpops.apkg')
