import csv
import datetime as dt
import re

import requests

from bs4 import BeautifulSoup

"""
This is a collection of tools used to scrape sites for hockey data.
"""

CONFIG = {
    'url': 'https://www.rotowire.com/daily/nhl/optimizer.php?site=DraftKings&sport=NHL',  # noqa
    'logger': {
        'levels': {
            'success': "\033[1;32;40m{prompt}\033[0m",
            'normal': "\033[1;36;40m{prompt}\033[0m",
            'warn': "\033[1;33;40m{prompt}\033[0m",
            'error': "\033[1;31;40m{prompt}\033[0m",
        },
    },
    'columns': [
        'first',
        'last',
        'salary',
        'position',
        'team',
        'opponent',
        'line',
        'power_play',
        'points',
    ],
    'skater_headers': [
        'First Name',
        'Last Name',
        'Salary',
        'Position',
        'Team',
        'Opponent',
        'Line',
        'Power_Play',
        'Projection',
    ],
    'goalie_headers': [
        'First Name',
        'Last Name',
        'Salary',
        'Team',
        'Opponent',
        'Projection',
    ],
}


class Player:
    def __init__(self, **kwargs):
        self.__dict__.update(
            (k, v) for k, v in kwargs.items() if k in CONFIG['columns']
        )

    def __str__(self):
        return self.__dict__


def log(message, action='parsing', priority='normal'):
    # Add color prompt
    prompt = "[{time}] {action}:"
    prompt = CONFIG['logger']['levels'][priority].format(prompt=prompt)
    print(
        prompt.format(
            time=dt.datetime.now().replace(second=0, microsecond=0),
            action=action,
        )
        + ' '
        + message
    )


def clean_name(field, target="\\n( )+\\xa0Confirmed"):
    field = field.strip()
    field = re.sub(target, '', field)
    return field


def field_from_row(row, field):
    return row.find('td', attrs={'class': 'rwo-{}'.format(field)})


def build_player_kwargs(row):
    # Hard code all values here for now
    full_name = field_from_row(row, 'name').text.strip()
    if any(full_name) is False or len(full_name.split()) < 2:
        full_name = "unknown unknown"
    salary = field_from_row(row, 'salary').attrs['data-salary'].strip()
    points = field_from_row(row, 'points').attrs['data-points'].strip()
    return {
        'first': clean_name(full_name).split()[0],
        'last': clean_name(full_name).split()[1],
        'salary': salary.replace(',', ''),
        'position': field_from_row(row, 'pos').text.strip(),
        'team': field_from_row(row, 'team').text.strip(),
        'opponent': field_from_row(row, 'opp').text.strip(' @'),
        'line': field_from_row(row, 'line').text.strip(),
        'power_play': field_from_row(row, 'line').text.strip(),
        'points': points
    }


def fetch_raw_data():
    """ Fetch data from rotowire by default """
    log("Fetching data...", action="fetching")
    response = requests.get(CONFIG['url'])
    if response.status_code != 200:
        log(
            "Error fetching data. "
            "Returned status code: {}".format(response.status_code),
            priority="error",
        )
        return

    log("Success", action="fetch", priority="success")
    return response.content


def parse_players(data, size=None):
    """ Parses a requests.response.content object for hockey players """
    log("Parsing HTML for players...", action="parsing")
    soup = BeautifulSoup(data, 'html.parser')
    table = soup.find_all('tr', attrs={'data-playerid': re.compile('[0-9]')})

    players = []
    try:
        for row in table:
            players.append(Player(**build_player_kwargs(row)))

    except ValueError as e:
        log(
            "Error parsing players: {}".format(e),
            priority="error",
        )

    if size:
        return players[:size]

    log("Success", action="parsing", priority='success')
    return players


def generate_csv(players):
    """ Generates a CSV from a list of player objects """
    skaters = [p for p in players if p.position != "G"]
    goalies = [g for g in players if g.position == "G"]

    log("Generating CSVs...", action="csv")
    with open('./skaters.csv', 'w') as skaterscsv:
        writer = csv.writer(skaterscsv)
        writer.writerow(CONFIG['skater_headers'])
        for skater in skaters:
            writer.writerow([
                skater.first,
                skater.last,
                skater.salary,
                skater.position,
                skater.team,
                skater.opponent,
                skater.line,
                skater.power_play,
                skater.points,
            ])

    with open('./goalies.csv', 'w') as goaliecsv:
        writer = csv.writer(goaliecsv)
        writer.writerow(CONFIG['goalie_headers'])
        for goalie in goalies:
            writer.writerow([
                goalie.first,
                goalie.last,
                goalie.salary,
                goalie.team,
                goalie.opponent,
                goalie.points,
            ])

    log("Success", action="csv", priority='success')


def main():
    data = fetch_raw_data()
    players = parse_players(data)
    generate_csv(players)


if __name__ == '__main__':
    main()
