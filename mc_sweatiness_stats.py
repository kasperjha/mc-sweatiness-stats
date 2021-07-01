from pathlib import Path
import json
import math
import requests
import argparse
import datetime


def get_stats_filepaths(server_directory):
    """ Get all stats filepaths from server_directory """
    server_directory = Path(server_directory)
    stats_directory = server_directory.joinpath('world', 'stats')
    return [path for path in stats_directory.iterdir() if path.is_file()]


def get_play_time_from_stats_file(stats_file_path):
    """ Collect filename and play_time from stats file. """
    with open(stats_file_path) as file:
        stats = json.load(file)
        return stats['stats']['minecraft:custom']['minecraft:play_time']


def get_playername_from_uuid(uuid):
    """ Use to mojang api to get playernames from uuid """
    response = requests.get(f'https://sessionserver.mojang.com/session/minecraft/profile/{uuid}')
    data = response.json()
    return data['name']


def parse_play_time(play_time):
    """ convert game_ticks to d,h,m,s """
    seconds = play_time/20
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    display_string = f'{math.floor(days)}days {math.floor(hours)}h {math.floor(minutes)}m'

    return display_string


def sort_players(players):
    """ sort players by play_time in decending order """
    return sorted(players, key=lambda k: k['play_time'], reverse=True)


def post_to_discord(webhook_url, players):
    """ update discord message """
    timestamp = datetime.datetime.now().strftime('%d.%m.%Y')
    players = sort_players(players)
    player_names = [player["name"] for player in players]
    play_times = [f'`{player["display_time"]}`' for player in players]
    data = {
        'embeds': [{
            'title': 'MC Sweatiness Stats :scroll: ',
            'footer': {'text': 'made by kasper | kakka.dev'},
            'fields': [
                {'name': 'Username', 'value': '\n'.join(player_names), 'inline': True},
                {'name': 'Playtime', 'value': '\n'.join(play_times), 'inline': True}
            ]
        }],
        'username': f'mcbot (kakka.dev) - {timestamp}'
    }
    return requests.post(webhook_url, json=data)


def main(server_dir, webhook_url):
    players = []
    for path in get_stats_filepaths(server_dir):
        # get values from function calls
        player_name = get_playername_from_uuid(path.stem)
        play_time = get_play_time_from_stats_file(path)
        display_time = parse_play_time(play_time)

        # create player dictionary object
        players.append({
            'name': player_name,
            'play_time': play_time,
            'display_time': display_time,
        })

    try:
        # post results to discord
        post_to_discord(webhook_url, players)
    except Exception as error:
        print(f'Posting to discord failed. {error}')


if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser(description='Get time played stats from server directory and post to discord.')
    parser.add_argument('server_dir', type=str, help='path to the server directory')
    parser.add_argument('webhook_url', type=str, help='path to the server directory')
    args = parser.parse_args()

    main(args.server_dir, args.webhook_url)
