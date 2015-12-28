import re
import requests

from cloudbot import hook
from cloudbot.util import web, formatting, timeformat

SC_RE = re.compile(r'(.*:)//(www.)?(soundcloud.com|snd.sc)(.*)', re.I)
API_BASE = 'http://api.soundcloud.com/{}/'


class APIError(Exception):
    pass


# DATA FETCHING
def get_with_search(endpoint, term):
    """
    Searches :endpoint on SoundCloud for :term and returns an item.
    :param endpoint: API endpoint to search
    :param term: Term to search for.
    :return:
    """
    try:
        params = {'client_id': api_key}
        if term != None:
          params['q'] = term
        request = requests.get(API_BASE.format(endpoint), params=params)
        request.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        raise APIError("Could not find {}: {}".format(endpoint, e))

    json = request.json()

    if not json:
        return None
    else:
        return json


def get_with_url(url):
    """
    Takes a SoundCloud URL and returns an item.
    :param url: URL to fetch data on.
    :return:
    """
    try:
        params = {'url': url, 'client_id': api_key}
        request = requests.get(API_BASE.format('resolve'), params=params)
        request.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        raise APIError("{}".format(e))

    json = request.json()

    if not json:
        return None
    else:
        return json


# DATA FORMATTING
def format_track(track, show_url=True):
    """
    Takes a SoundCloud track item and returns a formatted string.
    """
    out = track['title']

    out += " by \x02{}\x02".format(track['user']['username'])

    if track['genre']:
        out += " - \x02{}\x02".format(track['genre'])

    out += " - \x02{:,}\x02 plays, \x02{:,}\x02 favorites".format(track['playback_count'],
                                                                    track['favoritings_count'])

    if track['commentable']:
        out += ", \x02{:,}\x02 comments".format(track['comment_count'])

    if show_url:
        out += " - {}".format(web.try_shorten(track['permalink_url']))
    return out


def format_user(user, show_url=True):
    """
    Takes a SoundCloud user item and returns a formatted string.
    """
    out = "\x02{}\x02".format(user['username'])

    if user['description']:
        out += ': "{}"'.format(formatting.truncate(user['description']))

    if user['city']:
        out += ': {}'.format(user['city'])

    if user['country']:
        out += ", {}".format(formatting.truncate(user['country']))

    out += " - \x02{track_count:,}\x02 tracks, \x02{public_favorites_count:,}\x02 favourites, \x02{playlist_count:,}\x02 playlists, \x02{followers_count:,}\x02 " \
           "followers, \x02{followings_count:,}\x02 followed".format(**user)

    if show_url:
        out += " - {}".format(web.try_shorten(user['permalink_url']))

    return out

def format_user_favourites(user, show_url=True):
    """
    Takes a SoundCloud user item and returns their last 5 favourites.
    """
    out = "\x02{}\x02's fav. tracks:\n".format(user['username'])

    try:
        favs = get_with_url("https://soundcloud.com/%s/likes" % user['username'])
    except:
        return "Something went wrong!"

    if favs == None or len(favs) == 0:
        out += "No results found."
        return out

    if len(favs) > 5:
        favs = favs[0:5]

    for fav in favs:
        out += format_track(fav)
        out += "\n"

    return out

def format_user_tracks(user, show_url=True):
    """
    Takes a SoundCloud user item and returns their last 5 tracks.
    """
    out = "\x02{}\x02's tracks:\n".format(user['username'])

    try:
        tracks = get_with_search(("/users/%s/tracks" % user['id']), None)
    except:
        return "Something went wrong!"

    if tracks == None or len(tracks) == 0:
        out += "No results found."
        return out

    if len(tracks) > 5:
        tracks = tracks[0:5]

    for track in tracks:
        out += format_track(track)
        out += "\n"

    return out

def format_playlist(playlist, show_url=True):
    """
    Takes a SoundCloud playlist item and returns a formatted string.
    """
    out = "\x02{}\x02".format(playlist['title'])

    if playlist['description']:
        out += ': "{}"'.format(formatting.truncate(playlist['description']))

    if playlist['genre']:
        out += " - \x02{}\x02".format(playlist['genre'])

    out += " - by \x02{}\x02".format(playlist['user']['username'])

    if not playlist['tracks']:
        out += " - No items"
    else:
        out += " - {} items,".format(len(playlist['tracks']))

        seconds = round(int(playlist['duration'])/1000)
        out += " {}".format(timeformat.format_time(seconds, simple=True))

    if show_url:
        out += " - {}".format(web.try_shorten(playlist['permalink_url']))
    return out

def format_group(group, show_url=True):
    """
    Takes a SoundCloud group and returns a formatting string.
    """
    out = "\x02{}\x02".format(group['name'])

    if group['description']:
        out += ': "{}"'.format(formatting.truncate(group['description']))

    out += " - Owned by \x02{}\x02.".format(group['creator']['username'])

    if show_url:
        out += " - {}".format(web.try_shorten(group['permalink_url']))
    return out


# CLOUDBOT HOOKS
@hook.on_start()
def load_key(bot):
    global api_key
    api_key = bot.config.get("api_keys", {}).get("soundcloud", None)


@hook.command("soundcloud", "sc")
def soundcloud(text):
    """<query> -- Searches for tracks on SoundCloud."""
    if not api_key:
        return "This command requires a SoundCloud API key."
    try:
        track = get_with_search('tracks', text)[0]
    except APIError as ae:
        return ae

    if not track:
        return "No results found."

    try:
        return format_track(track)
    except APIError as ae:
        return ae


@hook.command("scuser")
def soundcloud_user(text):
    """<query> -- Searches for users on SoundCloud."""
    if not api_key:
        return "This command requires a SoundCloud API key."
    try:
        cmds = text.split(" ")
        user = get_with_search('users', cmds[0])[0]
    except APIError as ae:
        return ae

    if not user:
        return "No results found."

    try:
        if (len(cmds) > 1) and cmds[1] in ["favourites", "favs", "likes"]:
            return format_user_favourites(user)
        elif (len(cmds) > 1) and cmds[1] == "tracks":
            return format_user_tracks(user)
        return format_user(user)
    except APIError as ae:
        return ae


@hook.regex(SC_RE)
def soundcloud_url(match):
    if not api_key:
        return

    url = match.group(1).split(' ')[-1] + "//" + (match.group(2) if match.group(2) else "") + match.group(3) + \
        match.group(4).split(' ')[0]

    item = get_with_url(url)
    if not item:
        return

    if item['kind'] == 'track':
        return format_track(item, show_url=False)
    elif item['kind'] == 'user':
        return format_user(item, show_url=False)
    elif item['kind'] == 'playlist':
        return format_playlist(item, show_url=False)
    elif item['kind'] == 'group':
        return format_group(item, show_url=False)
