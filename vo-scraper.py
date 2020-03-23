#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Make sure you have `requests` -> pip3 install requests

Check README.md and LICENSE before using this program.
'''
# ========================================================================
#  ___                                      _
# |_ _|  _ __ ___    _ __     ___    _ __  | |_   ___
#  | |  | '_ ` _ \  | '_ \   / _ \  | '__| | __| / __|
#  | |  | | | | | | | |_) | | (_) | | |    | |_  \__ \
# |___| |_| |_| |_| | .__/   \___/  |_|     \__| |___/
#                   |_|
# ========================================================================

# Import urllib.request, urllib.parse, os, sys, http.client
import urllib.request, os, sys, http.client
from urllib.request import Request, urlopen
from sys import platform
import json     # For handling json files
import argparse # For parsing commandline arguments
import getpass  # For getting the user password


# Check whether `requests` is installed
try:
    import requests
except:
    print_information("Required package `requests` is missing, try installing with `pip3 install requests`", type='error')
    sys.exit(1)

# Check whether `webbrowser` is installed
try:
    import webbrowser # only used to open the user's browser when reporting a bug
except:
    print_information("Failed to import `webbrowser`. It is however not required for downloading videos", type='warning')

# ========================================================================
#   ____   _           _               _
#  / ___| | |   ___   | |__     __ _  | |   __   __   __ _   _ __   ___
# | |  _  | |  / _ \  | '_ \   / _` | | |   \ \ / /  / _` | | '__| / __|
# | |_| | | | | (_) | | |_) | | (_| | | |    \ V /  | (_| | | |    \__ \
#  \____| |_|  \___/  |_.__/   \__,_| |_|     \_/    \__,_| |_|    |___/
#
# ========================================================================

# Links to repo
gitlab_repo_page = "https://gitlab.ethz.ch/tgeorg/vo-scraper/"
gitlab_issue_page = gitlab_repo_page+"issues"
gitlab_changelog_page = gitlab_repo_page+"-/tags/v"
remote_version_link = gitlab_repo_page+"raw/master/VERSION"
program_version = '1.2'

# For web requests
user_agent = 'Mozilla/5.0'
cookie_jar = requests.cookies.RequestsCookieJar()

# Store video sources in global list
video_src_collection = list()

# For stats
link_counter = 0
download_counter = 0
skip_counter = 0

#
series_metadata_suffix = ".series-metadata.json"
video_info_prefix = "https://video.ethz.ch/.episode-video.json?recordId="
directory_prefix = "Lecture Recordings" + os.sep

# Default quality
video_quality = "high"

# Boolean flags
download_all = False
verbose = False
print_src = False

# Location of text files
file_to_print_src_to = ""
history_file = ""

quality_dict = {
    'high'  : 0,
    'medium': 1,
    'low'   : 2
}

class bcolors:
    INFO = '\033[94m'
    ERROR = '\033[91m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'

print_type_dict = {
    'info'    : f"({bcolors.INFO}INF{bcolors.ENDC})",
    'warning' : f"({bcolors.WARNING}WRN{bcolors.ENDC})",
    'error'   : f"({bcolors.ERROR}ERR{bcolors.ENDC})"
}

# ===============================================================
#  _____                          _     _
# |  ___|  _   _   _ __     ___  | |_  (_)   ___    _ __    ___
# | |_    | | | | | '_ \   / __| | __| | |  / _ \  | '_ \  / __|
# |  _|   | |_| | | | | | | (__  | |_  | | | (_) | | | | | \__ \
# |_|      \__,_| |_| |_|  \___|  \__| |_|  \___/  |_| |_| |___/
#
# ===============================================================

def print_information(str, type='info', verbose_only=False):
    """Print provided string.

    Keyword arguments:
    type         -- The type of information: {info, warning, error}
    verbose_only -- If true the string will only be printed when the verbose flag is set.
                    Useful for printing debugging info.
    """
    global print_type_dict

    if not verbose_only:
        if type == 'info' and not verbose:
            # Print without tag
            print(str)
        else:
            # Print with tag
            print(print_type_dict[type], str)
    elif verbose:
        # Always print with tag
        print(print_type_dict[type],str)

def get_credentials(user, passw):
    """Gets user credentials and returns them

    Keyword arguments:
    user  -- The username passed from a text file
    passw -- The password passed from a text file
    """
    if not user:
        user  = input("Enter your username: ")
    if not passw:
        passw = getpass.getpass()

    return(user, passw)

def acquire_login_cookie(protection, vo_link, user, passw):
    """Gets login-cookie by sending user credentials to login server

    Keyword arguments:
    protection  -- The type of login the lecture requires (NETHZ or custom password)
    vo_link     -- The link to the lecture
    user        -- The username passed from a text file
    passw       -- The password passed from a text file
    """
    global user_agent

    # Setup cookie_jar
    cookie_jar = requests.cookies.RequestsCookieJar()

    if protection == "ETH":
        print_information("This lecture requires a NETHZ login")
        while True:
            (user, passw) = get_credentials(user, passw)

            # Setup headers and content to send
            headers = { "Content-Type": "application/x-www-form-urlencoded", "CSRF-Token": "undefined", 'User-Agent': user_agent}
            data = { "__charset__": "utf-8", "j_validate": True, "j_username": user, "j_password": passw}

            # Request login-cookie
            r = requests.post("https://video.ethz.ch/j_security_check", headers=headers, data=data)

            # Put login cookie in cookie_jar
            cookie_jar = r.cookies
            if cookie_jar:
                break
            else:
                print_information("Wrong username or password, please try again", type='warning')
                (user, passw) = ('', '') # Reset passed credentials to not end up in loop if wrong credentials were passed

    elif protection == "PWD":
        print_information("This lecture requires a CUSTOM login. Check the lecture's website or your emails for the credentials.")

        while True:
            (user, passw) = get_credentials(user, passw)

            # Setup headers and content to send
            headers = {"Referer": vo_link+".html", "User-Agent":user_agent}
            data = { "__charset__": "utf-8", "username": user, "password": passw }

            # Get login cookie
            r = requests.post(vo_link+".series-login.json", headers=headers, data=data)

            # Put login cookie in cookie_jar
            cookie_jar = r.cookies
            if cookie_jar:
                break
            else:
                print_information("Wrong username or password, please try again", type='warning')
                (user, passw) = ('', '') # Reset passed credentials to not end up in loop if wrong credentials were passed

    else:
        print_information("Unknown protection type: " + protection, type='error')
        print_information("Please report this to the project's GitLab issue page!", type='error')
        report_bug()

    print_information("Acquired cookie:", verbose_only=True)
    print_information(cookie_jar, verbose_only=True)

    return cookie_jar

def pretty_print_episodes(vo_json_data, selected):
    """Prints the episode numbers that match `selected`"""
    # Get length of longest strings for nice formatting when printing
    nr_length = len(" Nr.")
    max_date_length = max([len(str(episode['createdAt'][:-6])) for episode in vo_json_data['episodes']])
    max_title_length = max([len(episode['title']) for episode in vo_json_data['episodes']])
    max_lecturer_length = max([len(str(episode['createdBy'])) for episode in vo_json_data['episodes']])

    # Print header
    print_information(
        " Nr."
        + " | " +
        "Date".ljust(max_date_length)
        + " | " +
        "Name".ljust(max_title_length)
        + " | " +
        "Lecturer".ljust(max_lecturer_length)
    )

    # Print the selected episodes
    for episode_nr in selected:
        episode = vo_json_data['episodes'][episode_nr]
        print_information(
            "%3d".ljust(nr_length) % episode_nr
            + " | " +
            episode['createdAt'][:-6].ljust(max_date_length)
            + " | " +
            episode['title'].ljust(max_title_length)
            + " | " +
            str(episode['createdBy']).ljust(max_lecturer_length)
        )


def vo_scrapper(vo_link, user, passw):
    """
    Gets the list of all available videos for a lecture.
    Allows user to select multiple videos.
    Returns the selected episodes

    Keyword arguments:
    vo_link -- The link to the lecture
    user    -- The username passed from a text file
    passw   -- The password passed from a text file

    Returns:
    A tuple consisting out of the filename and the video_src_link
    """
    global user_agent
    global download_all

    global video_quality
    global quality_dict
    global cookie_jar

    global series_metadata_suffix
    global video_info_prefix
    global directory_prefix

    global link_counter

    # Remove `.html` file extension
    if vo_link.endswith('.html'):
        vo_link = vo_link[:-5]

    # Get lecture metadata for episode list
    r = requests.get(vo_link + series_metadata_suffix, headers={'User-Agent': user_agent})
    vo_json_data = json.loads(r.text)

    # Increase counter for stats
    link_counter += len(vo_json_data['episodes'])

    # Print available lectures
    pretty_print_episodes(vo_json_data, range(len(vo_json_data['episodes'])))

    # Get video selections
    choice = list()
    if download_all:
        # Add all available videos to the selected
        choice = list(range(len(vo_json_data['episodes'])))
    else:
        # Let user pick videos
        try:
            choice = [int(x) for x in input(
                "Enter numbers of the above lectures you want to download separated by space (e.g. 0 5 12 14)\nJust press enter if you don't want to download anything from this lecture\n"
            ).split()]
        except:
            print()
            print_information("Exiting...")
            sys.exit()

    # Print the user's choice
    if not choice:
        print_information("No videos selected")
        return list() # Nothing to do anymore
    else:
        print_information("You selected:")
        pretty_print_episodes(vo_json_data, choice)
    print()

    # Check whether lecture requires login and get credentials if necessary
    print_information("Protection: " + vo_json_data["protection"], verbose_only=True)
    if vo_json_data["protection"] != "NONE":
        try:
            cookie_jar.update(acquire_login_cookie(vo_json_data["protection"], vo_link, user, passw))
        except KeyboardInterrupt:
            print()
            print_information("Keyboard interrupt detected, skipping lecture", type='warning')
            return

    local_video_src_collection = list()

    # Collect links for download
    for item_nr in choice:
        # Get link to video metadata json file
        item = vo_json_data['episodes'][item_nr]
        video_info_link = video_info_prefix+item['id']

        # Download the video metadata file
        # Use login-cookie if provided otherwise make request without cookie
        if(cookie_jar):
            r = requests.get(video_info_link, cookies=cookie_jar, headers={'User-Agent': user_agent})
        else:
            r = requests.get(video_info_link, headers={'User-Agent': user_agent})
        if(r.status_code == 401):
            # The lecture requires a login
            print_information("Received 401 response. The following lecture requires a valid login cookie:", type='error')
            item = vo_json_data['episodes'][item_nr]
            print_information("%2d" % item_nr + " " + item['title'] + " " + str(item['createdBy']) + " " + item['createdAt'][:-6], type='error')
            print_information("Make sure your token is valid. See README.md on how to acquire it.", type='error')
            print()
            continue
        video_json_data = json.loads(r.text)


        # Put available versions in list for sorting by video quality
        counter = 0
        versions = list()
        print_information("Available versions:", verbose_only=True)
        for vid_version in video_json_data['streams'][0]['sources']['mp4']:
            versions.append((counter, vid_version['res']['w']*vid_version['res']['h']))
            print_information(str(counter) + ": " + "%4d" %vid_version['res']['w'] + "x" + "%4d" %vid_version['res']['h'], verbose_only=True)
            counter += 1
        versions.sort(key=lambda tup: tup[1], reverse=True)
        # Now it's sorted: high -> medium -> low

        # Get video src url from json
        try: # try/except block to handle cases were not all three types of quality exist
            video_src_link = video_json_data['streams'][0]['sources']['mp4'][versions[quality_dict[video_quality]][0]]['src']
        except IndexError:
            print_information("Requested quality \"" + video_quality + "\" not available. Skipping episode!", type='error')
            continue

        lecture_title = vo_json_data['title']
        episode_title   = vo_json_data["episodes"][item_nr]["title"]

        # If video and lecture title overlap, remove lecture title from video title
        if episode_title.startswith(lecture_title):
            episode_title = episode_title[len(lecture_title):]

        # Extract episode name before adding the date to episode_title
        episode_name = item['createdAt'][:-6] + " " + lecture_title + episode_title

        # Append date
        episode_title = item['createdAt'][:-6]+episode_title

        # Filename is `directory/<video date (YYYY-MM-DD)><leftovers from video title>-<quality>.mp4`
        directory = directory_prefix + lecture_title + os.sep
        file_name = directory+episode_title+"_"+video_quality+".mp4"
        print_information(file_name, verbose_only=True)

        local_video_src_collection.append((file_name, video_src_link, episode_name))

    return local_video_src_collection

def downloader(file_name, video_src_link, episode_name):
    """Downloads the video and gives progress information

    Keyword arguments:
    file_name      -- Name of the file to write the data to
    video_src_link -- The link to download the data from
    episode_name   -- Name of the episode
    """
    global download_counter
    global skip_counter

    global print_src
    global file_to_print_src_to

    # Check for print_src flag
    if print_src:
        # Print to file if given
        if file_to_print_src_to:
            print_information("Printing " + video_src_link + "to file: "+ file_to_print_src_to, verbose_only=True)
            with open(file_to_print_src_to,"a") as f:
                f.write(video_src_link+"\n")
        else:
            print_information(video_src_link)
    # Otherwise download video
    else:
        print_information("Video source: " + video_src_link, verbose_only=True)

        # Check history file (if one has been specified) whether episode has already been downloaded
        if history_file:
            try:
                with open(history_file, "r") as file:
                    if video_src_link in [line.rstrip('\n') for line in file.readlines()]:
                        print("download skipped - file already recorded in history: " + episode_name)
                        skip_counter += 1
                        return
                    else:
                        print_information("Link has not yet been recorded in history file", verbose_only=True)
            except FileNotFoundError:
                print_information("No history file found at specified location: " + history_file, type='warning', verbose_only=True)

        # Create directory for video if it does not already exist
        directory = os.path.dirname(os.path.abspath(file_name))
        if not os.path.isdir(directory):
            os.makedirs(directory)
            print_information("This folder was generated: " + directory, verbose_only=True)
        else:
            print_information("This folder already exists: " + directory, verbose_only=True)

        # Check if file already exists
        if os.path.isfile(file_name):
            print_information("download skipped - file already exists: " + episode_name)
            skip_counter += 1
        # Otherwise download it
        else:
            # cf.: https://stackoverflow.com/questions/15644964/python-progress-bar-and-downloads
            with open(file_name+".part", "wb") as f:
                response = requests.get(video_src_link, stream=True)
                total_length = response.headers.get('content-length')

                print_information("Downloading " + episode_name + " (%.2f" % (int(total_length)/1024/1024) + " MiB)")

                if total_length is None: # We received no content length header
                    f.write(response.content)
                else:
                    # Download file and show progress bar
                    dl = 0
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        done = int(50 * dl / total_length)
                        sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)) )
                        sys.stdout.flush()
            print()

            # Remove `.part` suffix from file name
            os.rename(file_name+".part", file_name)
            print_information("Downloaded file: " + episode_name)
            download_counter += 1

        if history_file:
            # Regardless whether we just downloaded the file or it already exists on disk, we want to add it to the history file
            with open(history_file, "a") as file:
                file.write(video_src_link + '\n')

def check_connection():
    """Checks connection to video.ethz.ch and if it fails then also to the internet"""
    try:
        print_information("Checking connection to video.ethz.ch", verbose_only=True)
        req = Request('https://video.ethz.ch/', headers={'User-Agent': 'Mozilla/5.0'})
        urllib.request.urlopen(req)
    except urllib.error.URLError:
        try:
            print_information("There seems to be no connection to video.ethz.ch", type='error')
            print_information("Checking connection to the internet by connecting to duckduckgo.com", verbose_only=True)
            urllib.request.urlopen('https://www.duckduckgo.com')
        except urllib.error.URLError:
            print_information("There seems to be no internet connection - please connect to the internet and try again.", type='error')
        sys.exit(1)

def report_bug():
    """Opens GitLab issue page in browser"""
    print_information(gitlab_issue_page)
    try:
        input("Press enter to open the link in your browser or Ctrl+C to exit.")
        webbrowser.open(gitlab_issue_page)
    except:
        print()
    print_information("Exiting...")
    sys.exit(0)

def version_tuple(version):
    """Takes a string and turns into an integer tuple, splitting on `.`"""
    return tuple(map(int, (version.split('.'))))

def check_update():
    """
    Checks for a new version of the scraper and prompts the user if a new version is available
    """
    global program_version
    global remote_version_link
    global gitlab_repo_page
    global gitlab_changelog_page

    print_information("Checking for update", verbose_only=True)

    # try/except block to not crash the scraper just because it couldn't connect to server holding the version number
    try:
        r = requests.get(remote_version_link)
        remote_version_string = r.text

        if r.status_code == 200: # Loading the version number succeeded

            remote_version = version_tuple(remote_version_string)
            local_version = version_tuple(program_version)


            if remote_version > local_version:
                # There's an update available, prompt the user
                print_information("A new version of the VO-scraper is available: " + '.'.join(map(str,remote_version)), type='warning')
                print_information("You have version: " + '.'.join(map(str,local_version)), type='warning')
                print_information("You can download the new version from here: " + gitlab_repo_page, type='warning')
                print_information("The changelog can be found here: " + gitlab_changelog_page + '.'.join(map(str,remote_version)), type='warning')
                print_information("Press enter to continue with the current version", type='warning')
                input()
            else:
                # We are up to date
                print_information("Scraper is up to date according to version number in remote repo.", verbose_only=True)
        else:
            raise Exception # We couldn't get the file for some reason
    except:
        # Update check failed
        print_information("Update check failed, skipping...", type='warning')
        # Note: We don't want the scraper to fail because it couldn't check for a new version so we continue regardless

def read_links_from_file(file):
    """Reads the links from a text file
    Each link should be on a seperate line
    Lines starting with `#` will be ignored
    Username and password can be added at the end of the link seperated by a space
    """
    links = list()
    if os.path.isfile(file):
        # Read provided file
        with open(file, "r") as myfile:
            file_links = myfile.readlines()

        # Strip lines containing a `#` symbol as they are comments
        file_links = [line for line in file_links if not line.startswith('#')]

        # Strip newline characters
        file_links = [x.rstrip('\n') for x in file_links]

        # Strip empty lines
        file_links = [line for line in file_links if line]

        # Add links from file to the list of links to look at
        links += file_links
    else:
        print_information("No file with name \"" + file +"\" found", type='error')
    return links

def apply_args(args):
    """Applies the provided command line arguments
    The following are handled here:
     - verbose
     - bug
     - all
     - quality
     - print-src
     - destination
     - history
    """

    global verbose
    global download_all
    global video_quality
    global print_src
    global file_to_print_src_to
    global directory_prefix
    global history_file

    # Enable verbose for debugging
    verbose = args.verbose
    print_information("Verbose enabled", verbose_only=True)

    # Check if user wants to submit bug report and exit
    if(args.bug == True):
        print_information("If you found a bug you can raise an issue here: ")
        report_bug()

    # Set global variable according to input
    download_all = args.all
    video_quality = args.quality

    # Check for printing flag
    if hasattr(args, 'print_src'):
        print_src=True
        # Store where to print video source
        if args.print_src:
            file_to_print_src_to = args.print_src

    # Check for destination flag
    if args.destination:
        directory_prefix = args.destination
        print_information("The user passed directory is: " + directory_prefix, verbose_only=True)
        if not directory_prefix.endswith(os.sep):
            # Add trailing (back)slash as the user might have forgotten it
            directory_prefix += os.sep
            print_information("Added missing slash: " + directory_prefix, verbose_only=True)

    # Store where to read/print history
    if args.history:
        history_file = args.history
        print_information("History file location: " + history_file, verbose_only= True)


def setup_arg_parser():
    """Sets the parser up to handle all possible flags"""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "lecture_link",
        nargs='*',
        help="A link for each lecture you want to download videos from. The link should look like: https://video.ethz.ch/lectures/<department>/<year>/<spring or autumn>/<Number>.html"
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Download all videos of the specified lecture. Already downloaded video will be skipped."
    )
    parser.add_argument(
        "-b", "--bug",
        action="store_true",
        help="Print link to GitLab issue page and open it in browser."
    )
    parser.add_argument(
        "-d", "--destination",
        help="Directory where to save the files to. By default this is the folder \"Lecture Recordings/\" of the current working directory."
    )
    parser.add_argument(
        "-f", "--file",
        help="A file with links to all the lectures you want to download. Each lecture link should be on a new line. See README.md for details."
    )
    parser.add_argument(
        "-hs", "--history",
        help="A file to which the scraper saves the IDs of downloaded videos to. The scraper will skip downloads if the corresponding ID exists in the specified file."
    )
    parser.add_argument(
        "-p", "--print-src",
        metavar="FILE",
        nargs="?",
        default=argparse.SUPPRESS,
        help="Prints the source link for each video but doesn't download it. Follow with filename to print to that file instead. Useful if you want to use your own tool to download the video."
    )
    parser.add_argument(
        "-q", "--quality",
        choices=['high','medium','low'],
        default='high',
        help="Select video quality. Accepted values are \"high\" (1920x1080), \"medium\" (1280x720), and \"low\" (640x360). Default is \"high\""
    )
    parser.add_argument(
        "-sc", "--skip-connection-check",
        action="store_true",
        help="Skip checking whether there's a connection to video.ethz.ch or the internet in general."
    )
    parser.add_argument(
        "-su", "--skip-update-check",
        action="store_true",
        help="Skip checking whether there's an update available for the scraper"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print additional debugging information."
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version number and exit."
    )
    return parser

def print_usage():
    """Prints basic usage of parser and gives examples"""
    print_information("You haven't added any lecture links! To download a lecture video you need to pass a link to the lecture, e.g.:")
    print_information("    \"python3 vo-scraper.py https://video.ethz.ch/lectures/d-infk/2019/spring/252-0028-00L.html\"")
    print_information("")
    print_information("You can also pass optional arguments. For example, the following command downloads all lectures of \"Design of Digital Circuits\" from the year 2019 in low quality:")
    print_information("    \"python3 vo-scraper.py --quality low --all https://video.ethz.ch/lectures/d-infk/2019/spring/252-0028-00L.html\"")
    print_information("")
    print_information("To see all possible arguments run \"python3 vo-scraper.py --help\"")

def remove_illegal_characters(str):
    """Removes characters that are deemed illegal in some file systems such as NTFS from the input string

    Keyword arguments:
    str -- The string from which to remove the characters
    """
    illegal_chars = '?<>:*|"^'
    for c in illegal_chars:
        str = str.replace(c,'')
    return str

# ===============================================================
#  __  __           _
# |  \/  |   __ _  (_)  _ __
# | |\/| |  / _` | | | | '_ \
# | |  | | | (_| | | | | | | |
# |_|  |_|  \__,_| |_| |_| |_|
#
# ===============================================================

if __name__ == '__main__':
    # Setup parser
    parser = setup_arg_parser()
    args = parser.parse_args()

    # Check for version flag
    if args.version:
        print_information(program_version)
        sys.exit()

    # Apply commands from input
    apply_args(args)

    # Collect lecture links
    links = list()
    if args.file:
        links += read_links_from_file(args.file)

    # Append links passed through the command line:
    links += args.lecture_link

    # Extract username and password from "link"
    lecture_objects = list()
    lecture_objects +=  [tuple((link.split(' ') + ['',''])[:3]) for link in links] # This gives us tuples of size 3, where user and pw can be empty

    # Print basic usage and exit if no lecture links are passed
    if not links:
        print_usage()
        sys.exit()

    # Connection check
    if not args.skip_connection_check:
        check_connection()
    else:
        print_information("Connection check skipped.", verbose_only=True)

    # Update check
    if not args.skip_update_check:
        check_update()
    else:
        print_information("Update check skipped.", verbose_only=True)

    # Run scraper for every link provided to get video sources for each episode
    for (link, user, password) in lecture_objects:
        print_information("Currently selected: " + link, verbose_only=True)
        if "video.ethz.ch" not in link:
            print_information("Looks like the provided link does not go to 'videos.ethz.ch' and has therefore been skipped. Make sure that it is correct: " + link, type='warning')
        else:
            video_src_collection += vo_scrapper(link, user, password)
        print()

    # Print collected episodes
    print_information(video_src_collection, verbose_only=True)

    # Strip illegal characters:
    video_src_collection = [(remove_illegal_characters(file_name), video_src_link, episode_name) for (file_name, video_src_link, episode_name) in video_src_collection]

    # Download selected episodes
    for (file_name, video_src_link, episode_name) in video_src_collection:
        downloader(file_name, video_src_link, episode_name)

    # Print summary and exit
    print_information(str(link_counter) + " files found, " + str(download_counter) + " downloaded and " + str(skip_counter) + " skipped")
    if platform == "win32":
        input('\nEOF') # So Windows users also see the output (apparently)
