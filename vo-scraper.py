#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Make sure you have `requests` -> pip3 install requests

Check README.md and LICENSE before using this program.
"""
# ========================================================================
#  ___                                      _
# |_ _|  _ __ ___    _ __     ___    _ __  | |_   ___
#  | |  | '_ ` _ \  | '_ \   / _ \  | '__| | __| / __|
#  | |  | | | | | | | |_) | | (_) | | |    | |_  \__ \
# |___| |_| |_| |_| | .__/   \___/  |_|     \__| |___/
#                   |_|
# ========================================================================

# Import urllib.request, urllib.parse, os, sys, http.client
import urllib.request
import os
import sys
from urllib.request import Request
import json  # For handling json files
import argparse  # For parsing commandline arguments
import getpass  # For getting the user password
import random  # For selecting a random hint
import shutil  # For getting terminal size
import webbrowser  # only used to open the user's browser when reporting a bug

# Check whether `requests` is installed
try:
    import requests
except:
    print(
        "(\033[91mERR\033[0m) Required package `requests` is missing, try installing with `pip3 install requests`"
    )
    sys.exit(-1)

# ========================================================================
#   ____   _           _               _
#  / ___| | |   ___   | |__     __ _  | |   __   __   __ _   _ __   ___
# | |  _  | |  / _ \  | '_ \   / _` | | |   \ \ / /  / _` | | '__| / __|
# | |_| | | | | (_) | | |_) | | (_| | | |    \ V /  | (_| | | |    \__ \
#  \____| |_|  \___/  |_.__/   \__,_| |_|     \_/    \__,_| |_|    |___/
#
# ========================================================================

# Links to repo
github_repo_page = "https://github.com/gteufelberger/vo-scraper/"
github_issue_page = github_repo_page + "issues"
github_changelog_page = github_repo_page + "releases"
remote_version_link = (
    "https://api.github.com/repos/gteufelberger/vo-scraper/releases/latest"
)
program_version = "4.0.0"

# For web requests
user_agent = "Mozilla/5.0"
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
video_quality = "HD"

# Boolean flags
download_all = False
download_latest = False
verbose = False
print_src = False
HIDE_PROGRESS_BAR = False

# Location of text files
file_to_print_src_to = ""
history_file = ""
PARAMETER_FILE = "parameters.txt"


class bcolors:
    INFO = "\033[94m"
    ERROR = "\033[91m"
    WARNING = "\033[93m"
    ENDC = "\033[0m"


print_type_dict = {
    "info": f"({bcolors.INFO}INF{bcolors.ENDC})",
    "warning": f"({bcolors.WARNING}WRN{bcolors.ENDC})",
    "error": f"({bcolors.ERROR}ERR{bcolors.ENDC})",
}

HINT_LIST = [
    # --help
    """Want to know more about the scrapers functionality?
Run `python3 vo-scraper.py --help` to see all commands that can be used with the scraper.
For a detailed explanation of some of the commands, check out the README here: https://gitlab.ethz.ch/tgeorg/vo-scraper""",
    # --all
    """Want to download all recordings of a lecture at once?
If you call the vo-scraper with `--all` it will skip the selection screen and will download all recordings instead.
Usage example:

    python3 vo-scraper.py --all https://video.ethz.ch/lectures/d-infk/2019/spring/252-0028-00L.html""",
    # --bug
    """Found a bug?
Run `python3 vo-scraper.py --bug` or report it directly at https://gitlab.ethz.ch/tgeorg/vo-scraper/issues""",
    # --destination DESTINATION
    """Did you know? By default the vo-scraper saves the dowloaded recordings in \""""
    + directory_prefix
    + """<name of lecture>\"
If you want the recordings saved in a different place you can use the parameter `--destination <your folder>`
For example:

    python3 vo-scraper.py --destination my_folder https://video.ethz.ch/lectures/d-infk/2019/spring/252-0028-00L.html

saves the recordings inside the folder name \"my_folder\"""",
    # --disable-hints
    """Getting annoyed by this hint message?
You can pass the parameter `--disable-hints` to not show hints after running.""",
    # --file FILE
    """Downloading multiple lectures and tired of having to enter all those links everytime you want to download a recording?
You can paste all your links in a text file and then tell the scraper to read from that file using the parameter `--file <your text file>`
Example:

    python3 vo-scraper.py --file my_lectures.txt

The scraper will read the links from that file and download them as usual.""",
    # --hide-progress-bar
    """Progress bar breaking your terminal?
Hide it by passing the parameter `--hide-progress-bar`""",
    # --history FILE
    """Did you know, that the scraper does not re-download a lecture recording if it detects the recording in its download folder?
This way bandwidth is saved by preventing unecessary re-downloads, especially when using the `--all` parameter to download all existing recordings of a lecture.
However this also mean that if you delete the recording and run the scraper with `--all` again it will re-download the recording.

To fix this you can use the parameter `--history <some filename>` which creates a text file with that name and stores a history of all downloaded lectures there.
For example:

    python3 vo-scraper.py --history history.txt <your links>

will create a file called 'history.txt' and save a history of all downloaded recordings there. If you delete a downloaded video the scraper will not redownload it as long as you pass `--history <filename> every time you run it.`""",
    # --parameter-file FILE
    """Annoyed by having to type all those parameters like `--all`, `--history`, etc. by hand?
You can create a text file called \""""
    + PARAMETER_FILE
    + """\" and paste all your parameters there. If it's in the same location as the scraper it will automatically read it and apply them.

If you want to use a different name for it, you can pass `--parameter-file <your filename>` to read parameters from `<your filename>` instead.
Ironically this parameter cannot be put into the parameter file.""",
    # --print-source [FILE]
    """Have your own method of downloading videos?
You can use the parameter `--print-source` to print the direct links to the recordings instead of downloading them.
By default the links are printed in your terminal. If you follow up the parameter with a file e.g. `--print-source video_links.txt` a file with that name is created and all the links are saved there.""",
    # --quality
    """Downloading recordings takes too long as the files are too big?
You can download different video resolutions using the `--quality` parameter together with desired resolution either as an integer or specified via a keyword like `HD`, `2K`, `4K`.
Example:

    python3 vo-scraper.py --quality 480p https://video.ethz.ch/lectures/d-infk/2019/spring/252-0028-00L.html

If the requested resolution does not exist, the scraper will pick the next closest one. Note that the default quality is 'HD'. If you always want the highest possible quality you can use `--quality highest`. Conversely if always want the lowest quality use `--quality lowest`""",
    # --skip-connection-check
    # --skip-update-check
    """In order to ensure functionality, the scraper will check whether your version is up to date and that you have a connection to video.ethz.ch (as well as the internet if video.ethz.ch fails).
If you don't like this, you can pass the parameter `--skip-update-check` to prevent looking for updates and `--skip-connection-check` to prevent checking for an internet connection.""",
]
# ===============================================================
#  _____                          _     _
# |  ___|  _   _   _ __     ___  | |_  (_)   ___    _ __    ___
# | |_    | | | | | '_ \   / __| | __| | |  / _ \  | '_ \  / __|
# |  _|   | |_| | | | | | | (__  | |_  | | | (_) | | | | | \__ \
# |_|      \__,_| |_| |_|  \___|  \__| |_|  \___/  |_| |_| |___/
#
# ===============================================================


def print_information(str, type="info", verbose_only=False):
    """Print provided string.

    Keyword arguments:
    type         -- The type of information: {info, warning, error}
    verbose_only -- If true the string will only be printed when the verbose flag is set.
                    Useful for printing debugging info.
    """
    global print_type_dict

    if not verbose_only:
        if type == "info" and not verbose:
            # Print without tag
            print(str)
        else:
            # Print with tag
            print(print_type_dict[type], str)
    elif verbose:
        # Always print with tag
        print(print_type_dict[type], str)


def get_credentials(user, passw):
    """Gets user credentials and returns them

    Keyword arguments:
    user  -- The username passed from a text file
    passw -- The password passed from a text file
    """
    if not user:
        user = input("Enter your username: ")
    if not passw:
        passw = getpass.getpass()

    return (user, passw)


def acquire_login_cookie(protection, vo_link, user, passw):
    """Gets login-cookie by sending user credentials to login server

    Keyword arguments:
    protection  -- The type of login the lecture requires (NETHZ or custom password)
    vo_link     -- The link to the lecture
    user        -- The username passed from a text file
    passw       -- The password passed from a text file

    Returns:
    Cookie jar containing the users valid authentication cookie
    """
    global user_agent

    # Setup cookie_jar
    cookie_jar = requests.cookies.RequestsCookieJar()

    if protection == "ETH":
        print_information("This lecture requires a NETHZ login")
        while True:
            (user, passw) = get_credentials(user, passw)

            # Setup headers and content to send
            headers = {"User-Agent": user_agent, "Referer": vo_link + ".html"}
            data = {
                "__charset__": "utf-8",
                "j_validate": True,
                "j_username": user,
                "j_password": passw,
            }

            # Request login-cookie
            r = requests.post(
                "https://video.ethz.ch/j_security_check", headers=headers, data=data
            )
            print_information(f"Received response: {r.status_code}", verbose_only=True)

            # Put login cookie in cookie_jar
            cookie_jar = r.cookies
            if cookie_jar:
                break
            else:
                print_information(
                    "Wrong username or password, please try again", type="warning"
                )
                (user, passw) = (
                    "",
                    "",
                )  # Reset passed credentials to not end up in loop if wrong credentials were passed

    elif protection == "PWD":
        print_information(
            "This lecture requires a CUSTOM login. Check the lecture's website or your emails for the credentials."
        )

        while True:
            (user, passw) = get_credentials(user, passw)

            # Setup headers and content to send
            headers = {"Referer": vo_link + ".html", "User-Agent": user_agent}
            data = {"__charset__": "utf-8", "username": user, "password": passw}

            # Get login cookie
            r = requests.post(
                vo_link + ".series-login.json", headers=headers, data=data
            )

            # Put login cookie in cookie_jar
            cookie_jar = r.cookies
            if cookie_jar:
                break
            else:
                print_information(
                    "Wrong username or password, please try again", type="warning"
                )
                (user, passw) = (
                    "",
                    "",
                )  # Reset passed credentials to not end up in loop if wrong credentials were passed

    else:
        print_information("Unknown protection type: " + protection, type="error")
        print_information(
            "Please report this to the project's GitLab issue page!", type="error"
        )
        report_bug()

    print_information("Acquired cookie:", verbose_only=True)
    print_information(cookie_jar, verbose_only=True)

    return cookie_jar


def pretty_print_episodes(vo_json_data, selected):
    """Prints the episode numbers that match `selected`"""
    # Get length of longest strings for nice formatting when printing
    nr_length = len(" Nr.")
    max_date_length = max(
        [len(str(episode["createdAt"][:10])) for episode in vo_json_data["episodes"]]
    )
    max_title_length = max(
        [len(episode["title"]) for episode in vo_json_data["episodes"]]
    )
    max_lecturer_length = max(
        [len(str(episode["createdBy"])) for episode in vo_json_data["episodes"]]
    )

    # Print header
    print_information(
        " Nr."
        + " | "
        + "Date".ljust(max_date_length)
        + " | "
        + "Name".ljust(max_title_length)
        + " | "
        + "Lecturer".ljust(max_lecturer_length)
    )

    # Print the selected episodes
    for episode_nr in selected:
        episode = vo_json_data["episodes"][episode_nr]
        print_information(
            f"{episode_nr:3d}".ljust(nr_length)
            + " | "
            + episode["createdAt"][:10].ljust(max_date_length)
            + " | "
            + episode["title"].ljust(max_title_length)
            + " | "
            + str(episode["createdBy"]).ljust(max_lecturer_length)
        )


def make_range(item, max_episode_number):
    """

    Keyword arguments:
    item               -- a string in the form of 'x..z' or 'x..y..z'
    max_episode_number -- The highest episode number to have an upperbound for the range of episodes

    Returns:
    A range from x to z, with step size y, 1 if y wasn't provided
    """
    if len(item.split("..")) == 2:
        # user passed something like 'x..z', so step size is 1
        lower_bound, upper_bound = item.split("..")
        step = 1
    else:
        # user passed something like 'x..y..z', so step size is y
        lower_bound, step, upper_bound = item.split("..")

    # set the bounds to the outer limits if no number was passed
    lower_bound = int(lower_bound) if lower_bound else 0
    upper_bound = int(upper_bound) if upper_bound else max_episode_number

    step = int(step)
    return range(lower_bound, upper_bound + 1, step)


def get_user_choice(max_episode_number):
    """
    Prompts the user to pick multiple episodes and returns them

    Keyword arguments:
    max_episode_number -- The highest episode number to have an upperbound for the range of episodes

    Returns:
    A list containg the user picked choices
    """
    # Prompt user
    user_input = input(
        "Enter numbers of the above lectures you want to download separated by space (e.g. 0 5 12 14)\nJust press enter if you don't want to download anything from this lecture\n"
    ).split()
    choice = list()
    for elem in user_input:
        if elem.isnumeric():
            choice.append(int(elem))
        else:
            choice += make_range(elem, max_episode_number)

    # make elements of `choice` unique
    choice = set(choice)
    # sort them, to download in order and not randomly
    choice = sorted(choice)

    return choice


def resolution_from_input(resolution):
    # Turn named resolution into number
    if resolution.lower() == "4k":
        resolution = "2160p"
    if resolution.lower() == "2k":
        resolution = "1440p"
    if resolution.lower() == "fullhd":
        resolution = "1080p"
    if resolution.lower() == "hd":
        resolution = "720p"
    if resolution.lower() == "sd":
        resolution = "480"
    if resolution.lower() == "high":
        resolution = "1080p"
    if resolution.lower() == "medium":
        resolution = "720p"
    if resolution.lower() == "low":
        resolution = "360p"

    # Parse the given video resolution
    return int(str(resolution).replace("p", ""))


def get_video_src_link_for_resolution(video_json_data, video_quality):
    """
    Takes the JSON data and requested quality and returns the direct link to that video stream.

    Keyword arguments:
    video_json_data -- JSON structure containing information about the requested recording
    video_quality   -- The desired video quality

    Returns:
    Direct link to the corresponding video stream based on desired resolution as well as the
    vertical resolution of the video.
    """
    # Put available resolutions in list for sorting by video quality
    counter = 0
    resolutions = list()
    print_information("Available resolutions:", verbose_only=True)
    for vid_version in video_json_data["streams"][0]["sources"]["mp4"]:
        resolutions.append((counter, vid_version["res"]["w"], vid_version["res"]["h"]))
        print_information(
            f"{str(counter)}: {vid_version['res']['w']:4}x{vid_version['res']['h']:4}",
            verbose_only=True,
        )
        counter += 1
    resolutions.sort(key=lambda tup: tup[1] * tup[2], reverse=True)
    # Now it's sorted: highest -> lowest

    # Get video src url from json
    if video_quality == "lowest":
        quality_index = -1
    elif video_quality == "highest":
        quality_index = 0
    else:
        video_quality_parsed = resolution_from_input(video_quality)

        # Subtract requested from available resolutions to get the closest one
        list_of_quality_diff = [
            (x[0], abs(video_quality_parsed - x[2])) for x in resolutions
        ]

        # Get the resolution closest to the requested one
        min_value = min(list_of_quality_diff, key=lambda t: t[1])
        quality_index = min_value[0]

        # Show a warning if the we cannot return the requested resolution
        if min_value[1] != 0:
            print_information(
                f"Requested quality {video_quality} not available, downloading {video_json_data['streams'][0]['sources']['mp4'][quality_index]['res']['h']}p instead",
                type="warning",
            )

    # Save actual quality of video for filename
    video_quality = (
        str(
            video_json_data["streams"][0]["sources"]["mp4"][
                resolutions[quality_index][0]
            ]["res"]["h"]
        )
        + "p"
    )

    video_src_link = video_json_data["streams"][0]["sources"]["mp4"][
        resolutions[quality_index][0]
    ]["src"]
    return video_src_link, video_quality


def vo_scrapper(vo_link, video_quality, user, passw):
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
    global download_latest

    global quality_dict
    global cookie_jar

    global series_metadata_suffix
    global video_info_prefix
    global directory_prefix

    global link_counter

    # Remove `.html` file extension
    vo_link = vo_link.replace(".html", "")

    # Remove `www.` prefix from domain name
    # If in link used as a referer during the authentication it causes a failure
    vo_link = vo_link.replace("www.", "")

    # Get lecture metadata for episode list
    r = requests.get(
        vo_link + series_metadata_suffix, headers={"User-Agent": user_agent}
    )
    # Try reading the received data as JSON.
    # If it fails, e.g. due to no lectures having been uploaded yet, we skip this lecture
    try:
        vo_json_data = json.loads(r.text)
    except json.decoder.JSONDecodeError:
        print_information(
            f"Could not get metadata for {vo_link}.html, skipping", type="warning"
        )
        return list()  # Return an empty list

    # Increase counter for stats
    link_counter += len(vo_json_data["episodes"])

    # Print available lectures
    pretty_print_episodes(vo_json_data, range(len(vo_json_data["episodes"])))

    # Get video selections
    choice = list()
    if download_all:
        # Add all available videos to the selected
        choice = list(range(len(vo_json_data["episodes"])))
    elif download_latest:
        # Only add newest video to the selected
        choice = [0]
    else:
        # Let user pick videos
        try:
            choice = get_user_choice(max(range(len(vo_json_data["episodes"]))))
        except KeyboardInterrupt:
            print()
            print_information("Exiting...")
            sys.exit()

    # Print the user's choice
    if not choice:
        print_information("No videos selected")
        return list()  # Nothing to do anymore
    else:
        print_information("You selected:")
        pretty_print_episodes(vo_json_data, choice)
    print()

    # Check whether lecture requires login and get credentials if necessary
    print_information("Protection: " + vo_json_data["protection"], verbose_only=True)
    if vo_json_data["protection"] != "NONE":
        try:
            cookie_jar.update(
                acquire_login_cookie(vo_json_data["protection"], vo_link, user, passw)
            )
        except KeyboardInterrupt:
            print()
            print_information(
                "Keyboard interrupt detected, skipping lecture", type="warning"
            )
            return

    local_video_src_collection = list()

    # Collect links for download
    for item_nr in choice:
        # Get link to video metadata json file
        item = vo_json_data["episodes"][item_nr]
        video_info_link = video_info_prefix + item["id"]

        # Print it for debbuging
        print_information(video_info_link, verbose_only=True)

        # Download the video metadata file
        # Use login-cookie if provided otherwise make request without cookie
        if cookie_jar:
            r = requests.get(
                video_info_link, cookies=cookie_jar, headers={"User-Agent": user_agent}
            )
        else:
            r = requests.get(video_info_link, headers={"User-Agent": user_agent})
        if r.status_code == 401:
            # The lecture requires a login
            print_information(
                "Received 401 response. The following lecture requires a valid login cookie:",
                type="error",
            )
            item = vo_json_data["episodes"][item_nr]
            print_information(
                f"{item_nr:2d} {item['title']} {str(item['createdBy'])} {item['createdAt'][:10]}",
                type="error",
            )
            print_information(
                "Make sure your token is valid. See README.md on how to acquire it.",
                type="error",
            )
            print()
            continue
        video_json_data = json.loads(r.text)

        # Get video src url from json based on resolution
        try:
            video_src_link, available_video_quality = get_video_src_link_for_resolution(
                video_json_data, video_quality
            )
        except IndexError:
            # Audio only lectures error out, skip them
            print_information(
                f"Couldn't get download link for recording {item_nr}. Skipping",
                type="warning",
            )
            continue

        lecture_title = vo_json_data["title"]
        episode_title = vo_json_data["episodes"][item_nr]["title"]

        # If video and lecture title overlap, remove lecture title from video title
        episode_title = episode_title.replace(lecture_title, "")

        # Extract episode name before adding the date to episode_title
        episode_name = item["createdAt"][:10] + " " + lecture_title + episode_title

        # Append date
        episode_title = item["createdAt"][:10] + episode_title

        # Generate a pseudo hash by using part of the filename of the online version (which appears to be a UUID)
        pseudo_hash = video_src_link.replace(
            "https://oc-vp-dist-downloads.ethz.ch/mh_default_org/oaipmh-mmp/", ""
        )[:8]
        print_information(pseudo_hash, verbose_only=True)

        # Filename is `directory/<video date (YYYY-MM-DD)><leftovers from video title>_<quality>-<pseudo_hash>.mp4`
        directory = directory_prefix + lecture_title + os.sep
        file_name = (
            directory
            + episode_title
            + "_"
            + available_video_quality
            + "-"
            + pseudo_hash
            + ".mp4"
        )
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
            print_information(
                "Printing " + video_src_link + "to file: " + file_to_print_src_to,
                verbose_only=True,
            )
            with open(file_to_print_src_to, "a") as f:
                f.write(video_src_link + "\n")
        else:
            print_information(video_src_link)
    # Otherwise download video
    else:
        print_information("Video source: " + video_src_link, verbose_only=True)

        # Check history file (if one has been specified) whether episode has already been downloaded
        if history_file:
            try:
                with open(history_file, "r") as file:
                    if video_src_link in [
                        line.rstrip("\n") for line in file.readlines()
                    ]:
                        print(
                            "download skipped - file already recorded in history: "
                            + episode_name
                        )
                        skip_counter += 1
                        return
                    else:
                        print_information(
                            "Link has not yet been recorded in history file",
                            verbose_only=True,
                        )
            except FileNotFoundError:
                print_information(
                    "No history file found at specified location: " + history_file,
                    type="warning",
                    verbose_only=True,
                )

        # Create directory for video if it does not already exist
        directory = os.path.dirname(os.path.abspath(file_name))
        if not os.path.isdir(directory):
            os.makedirs(directory)
            print_information(
                "This folder was generated: " + directory, verbose_only=True
            )
        else:
            print_information(
                "This folder already exists: " + directory, verbose_only=True
            )

        # Check if file already exists
        if os.path.isfile(file_name):
            print_information("download skipped - file already exists: " + episode_name)
            skip_counter += 1
        # Otherwise download it
        else:
            # cf.: https://stackoverflow.com/questions/15644964/python-progress-bar-and-downloads
            with open(file_name + ".part", "wb") as f:
                response = requests.get(video_src_link, stream=True)
                total_length = response.headers.get("content-length")

                print_information(
                    f"Downloading {episode_name} ({int(total_length) / 1024 / 1024:.2f} MiB)"
                )

                if total_length is None or HIDE_PROGRESS_BAR:
                    # We received no content length header...
                    # ... or user wanted to hide the progress bar
                    f.write(response.content)
                else:
                    # Download file and show progress bar
                    total_length = int(total_length)

                    try:
                        # Module with better progressbar
                        from tqdm import tqdm

                        # Setup progressbar
                        pbar = tqdm(
                            unit="B",
                            unit_scale=True,
                            unit_divisor=1024,
                            total=total_length,
                        )
                        pbar.clear()

                        # Download to file and update progressbar
                        for data in response.iter_content(chunk_size=4096):
                            pbar.update(len(data))
                            f.write(data)
                        # Close it
                        pbar.close()

                    # If tqdm is not installed, fallback to self-made version
                    except ModuleNotFoundError:
                        print_information(
                            "Optionally dependency tqdm not installed, falling back to built-in progressbar",
                            type="warning",
                            verbose_only=True,
                        )
                        dl = 0
                        for data in response.iter_content(chunk_size=4096):
                            dl += len(data)
                            f.write(data)
                            progressbar_width = shutil.get_terminal_size().columns - 2
                            done = int(progressbar_width * dl / total_length)
                            sys.stdout.write(
                                f"\r[{'=' * done}{' ' * (progressbar_width - done)}]"
                            )
                            sys.stdout.flush()
            print()

            # Remove `.part` suffix from file name
            os.rename(file_name + ".part", file_name)
            print_information("Downloaded file: " + episode_name)
            download_counter += 1

        if history_file:
            # Regardless whether we just downloaded the file or it already exists on disk, we want to add it to the history file
            with open(history_file, "a") as file:
                file.write(video_src_link + "\n")


def check_connection():
    """Checks connection to video.ethz.ch and if it fails then also to the internet"""
    try:
        print_information("Checking connection to video.ethz.ch", verbose_only=True)
        req = Request("https://video.ethz.ch/", headers={"User-Agent": "Mozilla/5.0"})
        urllib.request.urlopen(req)
    except urllib.error.URLError:
        try:
            print_information(
                "There seems to be no connection to video.ethz.ch", type="error"
            )
            print_information(
                "Checking connection to the internet by connecting to duckduckgo.com",
                verbose_only=True,
            )
            urllib.request.urlopen("https://www.duckduckgo.com")
        except urllib.error.URLError:
            print_information(
                "There seems to be no internet connection - please connect to the internet and try again.",
                type="error",
            )
        sys.exit(1)


def report_bug():
    """Opens GitLab issue page in browser"""
    print_information(github_issue_page)
    try:
        input("Press enter to open the link in your browser or Ctrl+C to exit.")
        webbrowser.open(github_issue_page)
    except:
        print()
    print_information("Exiting...")
    sys.exit(0)


def version_tuple(version):
    """Takes a string and turns into an integer tuple, splitting on `.`"""
    return tuple(map(int, (version.replace("v", "").split("."))))


def check_update():
    """
    Checks for a new version of the scraper and prompts the user if a new version is available
    """
    global program_version
    global remote_version_link
    global github_repo_page
    global github_changelog_page

    print_information("Checking for update", verbose_only=True)

    # try/except block to not crash the scraper just because it couldn't connect to server holding the version number
    try:
        r = requests.get(remote_version_link)
        remote_version_string = r.text

        if r.status_code == 200:  # Loading the version number succeeded
            latest_release = r.json()
            remote_version_string = latest_release["tag_name"]

            remote_version = version_tuple(remote_version_string)
            local_version = version_tuple(program_version)

            if remote_version > local_version:
                # There's an update available, prompt the user
                print_information(
                    "A new version of the VO-scraper is available: "
                    + ".".join(map(str, remote_version)),
                    type="warning",
                )
                print_information(
                    "You have version: " + ".".join(map(str, local_version)),
                    type="warning",
                )
                print_information(
                    "You can download the new version from here: " + github_repo_page,
                    type="warning",
                )
                print_information(
                    "The changelog can be found here: "
                    + github_changelog_page
                    + "/"
                    + remote_version_string,
                    type="warning",
                )
                print_information(
                    "Press enter to continue with the current version", type="warning"
                )
                input()
            else:
                # We are up to date
                print_information(
                    "Scraper is up to date according to version number in remote repo.",
                    verbose_only=True,
                )
        else:
            raise Exception  # We couldn't get the file for some reason
    except:
        # Update check failed
        print_information("Update check failed, skipping...", type="warning")
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
        file_links = [line for line in file_links if not line.startswith("#")]

        # Strip newline characters
        file_links = [x.rstrip("\n") for x in file_links]

        # Strip empty lines
        file_links = [line for line in file_links if line]

        # Add links from file to the list of links to look at
        links += file_links
    else:
        print_information('No file with name "' + file + '" found', type="error")
    return links


def apply_args(args):
    """Applies the provided command line arguments
    The following are handled here:
     - bug
     - all
     - hide-progress-bar
     - quality
     - print-source
     - destination
     - history
    """

    global download_all
    global download_latest
    global video_quality
    global print_src
    global file_to_print_src_to
    global directory_prefix
    global history_file
    global HIDE_PROGRESS_BAR

    # Check if user wants to submit bug report and exit
    if args.bug == True:
        print_information("If you found a bug you can raise an issue here: ")
        report_bug()

    # Set global variable according to input
    download_all = args.all
    download_latest = args.latest
    video_quality = args.quality
    HIDE_PROGRESS_BAR = args.hide_progress_bar

    # Check for printing flag
    if hasattr(args, "print_src"):
        print_src = True
        # Store where to print video source
        if args.print_src:
            file_to_print_src_to = args.print_src

    # Check for destination flag
    if args.destination:
        directory_prefix = args.destination
        print_information(
            "The user passed directory is: " + directory_prefix, verbose_only=True
        )
        if not directory_prefix.endswith(os.sep):
            # Add trailing (back)slash as the user might have forgotten it
            directory_prefix += os.sep
            print_information(
                "Added missing slash: " + directory_prefix, verbose_only=True
            )

    # Store where to read/print history
    if args.history:
        history_file = args.history
        print_information("History file location: " + history_file, verbose_only=True)


def setup_arg_parser():
    """Sets the parser up to handle all possible flags"""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "lecture_link",
        nargs="*",
        help="A link for each lecture you want to download videos from. The link should look like: https://video.ethz.ch/lectures/<department>/<year>/<spring or autumn>/<Number>.html",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Download all videos of the specified lecture. Already downloaded video will be skipped.",
    )
    parser.add_argument(
        "-b",
        "--bug",
        action="store_true",
        help="Print link to GitLab issue page and open it in browser.",
    )
    parser.add_argument(
        "-d",
        "--destination",
        help='Directory where to save the files to. By default this is the folder "'
        + directory_prefix
        + '" of the current working directory.',
    )
    parser.add_argument(
        "--disable-hints",
        action="store_true",
        help="If set no hints will be displayed if the scraper finished running",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="A file with links to all the lectures you want to download. Each lecture link should be on a new line. See README.md for details.",
    )
    parser.add_argument(
        "--hide-progress-bar",
        action="store_true",
        help="Hides the progress bar that is displayed while downloading a recording.",
    )
    parser.add_argument(
        "-hs",
        "--history",
        metavar="FILE",
        help="A file to which the scraper saves the IDs of downloaded videos to. The scraper will skip downloads if the corresponding ID exists in the specified file.",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Only downloads the latest video from each passed lecture.",
    )
    parser.add_argument(
        "--parameter-file",
        metavar="FILE",
        help="Pass the name of the file to read parameters from. If the flag is not set parser will try to read parameters from `parameters.txt`",
    )
    parser.add_argument(
        "-p",
        "--print-source",
        metavar="FILE",
        nargs="?",
        default=argparse.SUPPRESS,
        help="Prints the source link for each video but doesn't download it. Follow with filename to print to that file instead. Useful if you want to use your own tool to download the video.",
    )
    parser.add_argument(
        "-q",
        "--quality",
        default="HD",
        help="Select a specific video resolution. Either specify a height directly like `1080p` or use the keywords `FullHD`, `2K`, and `4K`. The scraper will try to download the video closest to the specified resolution. Additionally you can also use `highest` and `lowest` to always download the highest or lowest quality respectively.",
    )
    parser.add_argument(
        "-sc",
        "--skip-connection-check",
        action="store_true",
        help="Skip checking whether there's a connection to video.ethz.ch or the internet in general.",
    )
    parser.add_argument(
        "-su",
        "--skip-update-check",
        action="store_true",
        help="Skip checking whether there's an update available for the scraper",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print additional debugging information.",
    )
    parser.add_argument(
        "--version", action="store_true", help="Print version number and exit."
    )
    return parser


def print_usage():
    """Prints basic usage of parser and gives examples"""
    print_information(
        "You haven't added any lecture links! To download a lecture video you need to pass a link to the lecture, e.g.:"
    )
    print_information(
        '    "python3 vo-scraper.py https://video.ethz.ch/lectures/d-infk/2019/spring/252-0028-00L.html"'
    )
    print_information("")
    print_information(
        'You can also pass optional arguments. For example, the following command downloads all lectures of "Design of Digital Circuits" from the year 2019 in low quality:'
    )
    print_information(
        '    "python3 vo-scraper.py --quality low --all https://video.ethz.ch/lectures/d-infk/2019/spring/252-0028-00L.html"'
    )
    print_information("")
    print_information(
        'To see all possible arguments run "python3 vo-scraper.py --help"'
    )


def remove_illegal_characters(str):
    """Removes characters that are deemed illegal in some file systems such as NTFS from the input string

    Keyword arguments:
    str -- The string from which to remove the characters
    """
    illegal_chars = '?<>:*|"^'
    for c in illegal_chars:
        str = str.replace(c, "")
    return str


# ===============================================================
#  __  __           _
# |  \/  |   __ _  (_)  _ __
# | |\/| |  / _` | | | | '_ \
# | |  | | | (_| | | | | | | |
# |_|  |_|  \__,_| |_| |_| |_|
#
# ===============================================================


if __name__ == "__main__":
    # Setup parser
    parser = setup_arg_parser()
    args = parser.parse_args()

    # Enable verbose for debugging
    verbose = args.verbose
    print_information("Verbose enabled", verbose_only=True)

    # Check for version flag
    if args.version:
        print_information(program_version)
        sys.exit()

    # If a parameter file was passed, use that instead of default
    if args.parameter_file:
        PARAMETER_FILE = args.parameter_file
    # Read parameters if file exists
    if os.path.isfile(PARAMETER_FILE):
        with open(PARAMETER_FILE) as f:
            # Read file and remove trailing whitespaces and newlines
            parameters = [x.strip() for x in f.readlines()]
            # Remove comments i.e. lines starting with `#`
            parameters = [line for line in parameters if not line.startswith("#")]
            # Split strings with spaces
            parameters = [
                words for segments in parameters for words in segments.split()
            ]
            # Add parameters list
            sys.argv += parameters
            # Parse args again as we might have added some
            args = parser.parse_args()
    else:
        # Print when no parameter file was found
        # If no `--parameter-file` was passsed, this only prints when verbosity is turned on
        print_information(
            "No parameter file found at location: " + PARAMETER_FILE,
            verbose_only=not bool(args.parameter_file),
            type="warning",
        )

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
    lecture_objects += [
        tuple((link.split(" ") + ["", ""])[:3]) for link in links
    ]  # This gives us tuples of size 3, where user and pw can be empty

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

    # Print selected quality
    if video_quality == "lowest" or video_quality == "highest":
        quality_string = video_quality
    else:
        quality_string = str(resolution_from_input(video_quality)) + "p"
    print_information("Selected quality for downloads: " + quality_string)
    print_information("")

    # Run scraper for every link provided to get video sources for each episode
    for link, user, password in lecture_objects:
        print_information("Currently selected: " + link, verbose_only=True)
        if "video.ethz.ch" not in link:
            print_information(
                "Looks like the provided link does not go to 'videos.ethz.ch' and has therefore been skipped. Make sure that it is correct: "
                + link,
                type="warning",
            )

            # Give some useful information if the provided link goes to YouTube or Zoom
            if "youtube" in link or "youtu.be" in link:
                print_information(
                    "Note that if you want to download a lecture from YouTube, I recommend youtube-dl: https://github.com/ytdl-org/youtube-dl/"
                )
            if "zoom.us" in link:
                print_information(
                    "Note that if you want to download a lecture from Zoom, I recommend zoomdl: https://github.com/Battleman/zoomdl/"
                )

        else:
            video_src_collection += vo_scrapper(link, video_quality, user, password)
        print()

    # Print collected episodes
    print_information(video_src_collection, verbose_only=True)

    # Strip illegal characters:
    video_src_collection = [
        (remove_illegal_characters(file_name), video_src_link, episode_name)
        for (file_name, video_src_link, episode_name) in video_src_collection
    ]

    # Download selected episodes
    for file_name, video_src_link, episode_name in video_src_collection:
        downloader(file_name, video_src_link, episode_name)

    # Display hints if applicable
    if not args.disable_hints and HINT_LIST and video_src_collection:
        print()
        print("-" * shutil.get_terminal_size().columns)
        print("Hint:")
        print(random.choice(HINT_LIST))
        print("-" * shutil.get_terminal_size().columns)

    # Print summary and exit
    print_information(
        str(link_counter)
        + " files found, "
        + str(download_counter)
        + " downloaded and "
        + str(skip_counter)
        + " skipped"
    )
