#! /usr/bin/env python3
'''
Plex Library Viewer (Niema Moshiri 2024)
'''

# error message
def error(s):
    print(s, file=stderr); exit(1)

# imports
from sys import stderr
try:
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.shortcuts import input_dialog, message_dialog, radiolist_dialog
except:
    error("Unable to import 'prompt_toolkit'. Install via: 'pip install prompt_toolkit'")
try:
    from plexapi.myplex import MyPlexAccount
except:
    error("Unable to import 'plexapi'. Install via: 'pip install plexapi'")

# useful constants
VERSION = '0.0.1'
TOOL_NAME = 'Plex Library Viewer'
LINE_WIDTH = 120

# mapping from media types to human-readable text
MEDIA_TEXT = {
    'artist': 'Music Artist',
    'movie': 'Movie',
    'show': 'TV Show',
}

# text / messages
TEXT = {
    'prompt_password': "Please enter your My Plex password (append your 2FA code at the end if 2FA is enabled):",
    'prompt_username': "Please enter your My Plex username:",
    'select_movie': "Please select movie:",
    'select_server': "Please select Plex Media Server:",
    'select_server_media_type': "Please select media type:",
    'select_server_operation': "Please select an operation to perform on this Plex Media Server",
    'status_loading_all': "Loading all items from server (this might take a while)...",
    'title_error': HTML("<ansired>ERROR</ansired>"),
    'title_main': HTML("<ansiblue>%s v%s</ansiblue>" % (TOOL_NAME, VERSION)),
    'welcome': "Welcome to the %s! This simple tool aims to provide a user-friendly command-line interface for exploring Plex libraries using the Plex API.\n\nMade by Niema Moshiri (niemasd), 2024" % TOOL_NAME,
}

# break a long string into multiple lines
def break_string(s, max_width=LINE_WIDTH):
    col = 0; text = ''
    for word in s.split(' '):
        if col + len(word) + 1 >= max_width:
            text += '\n'; col = 0
        text += (word + ' '); col += (len(word) + 1)
    return text

# convert millisecond int to string
def ms_to_str(d):
    h = d // 3600000; d %= 3600000 # hours
    m = d //   60000; d %=   60000 # minutes
    s = d //    1000; d %=    1000 # seconds
    return '%s:%s:%s.%s' % (str(h).zfill(2), str(m).zfill(2), str(s).zfill(2), str(d).zfill(3))

# show welcome message
def show_welcome():
    message_dialog(title=TEXT['title_main'], text=TEXT['welcome']).run()

# sign into My Plex
def authenticate_myplex():
    username = input_dialog(title=TEXT['title_main'], text=TEXT['prompt_username']).run()
    if username is None:
        exit(1)
    password = input_dialog(title=TEXT['title_main'], text=TEXT['prompt_password']).run()
    if password is None:
        exit(1)
    account = MyPlexAccount(username, password)
    return account

# select Plex Media Server
def select_server(account):
    # iterate over MyPlexResource objects to find servers: https://python-plexapi.readthedocs.io/en/latest/modules/myplex.html#plexapi.myplex.MyPlexResource
    servers = list()
    for resource in account.resources():
        if 'server' in resource.provides.lower():
            servers.append((resource,resource.name))
    servers.sort(key=lambda x: x[1])
    selection = radiolist_dialog(title=TEXT['title_main'], text=TEXT['select_server'], values=servers).run()
    if selection is None:
        return None
    return selection.connect()

# select what you want to do with a Plex Media Server
def select_server_operation(server):
    values = [
        ('browse', HTML('<ansired>Browse</ansired> all media from all library sections')),
    ]
    values.sort(key=lambda x: x[1])
    return radiolist_dialog(title=server.friendlyName, text=TEXT['select_server_operation'], values=values).run()

# get all media from a server, and return as media_by_type[media_type] = list of media of that type
def server_list_all(server, verbose=True):
    if verbose:
        print(TEXT['status_loading_all'], end='\r')
    all_media = server.library.all()
    media_by_type = dict()
    for item in all_media:
        if item.type not in media_by_type:
            media_by_type[item.type] = list()
        media_by_type[item.type].append(item)
    if verbose:
        print(' '*len(TEXT['status_loading_all']), end='\r')
    return media_by_type

# view details about a single movie: https://python-plexapi.readthedocs.io/en/latest/modules/video.html#plexapi.video.Movie
def show_movie(movie):
    text = '<ansired>- Title:</ansired> %s' % movie.title
    if movie.editionTitle is not None:
        text += ' [%s]' % movie.editionTitle
    if movie.originalTitle is not None:
        text += '\n<ansired>- Original Title:</ansired> %s' % movie.originalTitle
    if movie.duration is not None:
        text += '\n<ansired>- Duration:</ansired> %s' % ms_to_str(movie.duration)
    if movie.originallyAvailableAt is not None:
        text += '\n<ansired>- Release Date:</ansired> %s' % movie.originallyAvailableAt.strftime("%Y-%m-%d")
    if movie.contentRating is not None:
        text += '\n<ansired>- Content Rating:</ansired> %s' % movie.contentRating
    if movie.rating is not None:
        text += '\n<ansired>- Critic Rating:</ansired> %s' % movie.rating
    message_dialog(title=server.friendlyName, text=HTML(text)).run()

# browse all media in this server
def server_operation_browse(server):
    media_by_type = server_list_all(server)
    while True:
        # pick media type (or exit)
        values = [(t, ("%s (%d items)" % (MEDIA_TEXT[t], len(l)))) for t, l in media_by_type.items()]
        values.sort(key=lambda x: x[1])
        media_type = radiolist_dialog(title=server.friendlyName, text=TEXT['select_server_media_type'], values=values).run()
        if media_type is None:
            break

        # list all movies
        elif media_type == 'movie':
            movies = [(movie, '%s (%d)' % (movie.title, movie.year)) for movie in media_by_type[media_type]]
            movies.sort(key=lambda x: x[1])
            while True:
                movie = radiolist_dialog(title='Movies (%s)' % server.friendlyName, text=TEXT['select_movie'], values=movies).run()
                if movie is None:
                    break
                show_movie(movie)

        # invalid media type (shouldn't get here)
        else:
            raise ValueError("Invalid media type: %s" % media_type)

# main content
if __name__ == "__main__":
    # authenticate account: https://python-plexapi.readthedocs.io/en/latest/modules/myplex.html#plexapi.myplex.MyPlexAccount
    show_welcome()
    account = authenticate_myplex()

    # main loop
    while True:
        # select server and operation: https://python-plexapi.readthedocs.io/en/latest/modules/server.html#plexapi.server.PlexServer
        server = select_server(account) # access Library via server.libary: https://python-plexapi.readthedocs.io/en/latest/modules/library.html#plexapi.library.Library
        if server is None:
            break
        server_operation = select_server_operation(server)

        # if no operation selected, re-prompt for server selection
        if server_operation is None:
            continue

        # browse all media
        elif server_operation == 'browse':
            server_operation_browse(server)

        # shouldn't get here
        else:
            raise ValueError("Invalid server operation: %s" % server_operation)
