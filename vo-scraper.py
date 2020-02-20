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

#import urllib.request, urllib.parse, os, sys, http.client
import urllib.request, os, sys, http.client
from urllib.request import Request, urlopen
from sys import platform
import json     # For handling json files
import argparse # For parsing commandline arguments
import getpass  # For getting the user password


# check whether `requests` is installed
try:
    import requests
except:
    print_information("Required package `requests` is missing, try installing with `pip3 install requests`", type='error')
    sys.exit(1)

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

user_agent = 'Mozilla/5.0'
login_token = ""
cookie_jar = requests.cookies.RequestsCookieJar()

#for stats
link_counter = 0
download_counter = 0
skip_counter = 0

series_metadata_suffix = ".series-metadata.json"
video_info_prefix = "https://video.ethz.ch/.episode-video.json?recordId="
directory_prefix = "Lecture Recordings/"

gitlab_issue_page = "https://gitlab.ethz.ch/tgeorg/vo-scraper/issues"

video_quality = "high"

download_all = False
verbose = False

print_src = False
file_to_print_src_to = ""

quality_dict = {
    'low'   : 0,
    'medium': 1,
    'high'  : 2
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
            # print without tag
            print(str)
        else:
            # print with tag
            print(print_type_dict[type], str)
    elif verbose:
        # Always print with tag
        print(print_type_dict[type],str)

def get_credentials():
    """Gets user credentials and returns them"""
    user  = input("Enter your username: ")
    passw = getpass.getpass()
    
    return(user, passw)

def acquire_login_cookie(protection, vo_link):
    """Gets login-token by sending user credentials to login server"""
    global user_agent

    # setup cookie_jar    
    cookie_jar = requests.cookies.RequestsCookieJar()

    if protection == "ETH":
        print_information("This lecture requires a NETHZ login")
        while True:
            (user, passw) = get_credentials()
            
            # setup headers and content to send
            headers = { "Content-Type": "application/x-www-form-urlencoded", "CSRF-Token": "undefined", 'User-Agent': user_agent}
            data = { "__charset__": "utf-8", "j_validate": True, "j_username": user, "j_password": passw}
            
            # request login-token
            r = requests.post("https://video.ethz.ch/j_security_check", headers=headers, data=data)

            # put login cookie in cookie_jar
            cookie_jar = r.cookies
            if cookie_jar:
                break
            else:
                print_information("Wrong username or password, please try again", type='warning')
    
    elif protection == "PWD":
        print_information("This lecture requires a CUSTOM login. Check lecture website or your emails for the credentials")
        
        while True:
            (user, passw) = get_credentials()

            # setup headers and content to send
            headers = {"Referer": vo_link+".html", "User-Agent":user_agent}
            data = { "__charset__": "utf-8", "username": user, "password": passw }

            # get login cookie
            r = requests.post(vo_link+".series-login.json", headers=headers, data=data)
            
            # put login cookie in cookie_jar
            cookie_jar = r.cookies
            if cookie_jar:
                break
            else:
                print_information("Wrong username or password, please try again", type='warning')
        
    else:
        print_information("Unknown protection type: " + protection, type='error') 
        print_information("Please report this to the project's GitLab issue page!", type='error')
        report_bug()

    print_information("Acquired cookie:", verbose_only=True)
    print_information(cookie_jar, verbose_only=True)
    
    return cookie_jar

def vo_scrapper(vo_link):
    """
    Gets the list of all available videos for a lecture.
    Allows user to select multiple videos.
    Afterwards passes the links to the video source to `downloader()`
    """
    global user_agent
    global link_counter
    global download_all

    global video_quality
    global quality_dict
    global login_token
    global cookie_jar

    global print_src
    global file_to_print_src_to

    global series_metadata_suffix
    global video_info_prefix
    global directory_prefix

    # remove `.html` file extension
    if vo_link.endswith('.html'):
        vo_link = vo_link[:-5]

    # get lecture metadata for episode list
    r = requests.get(vo_link + series_metadata_suffix, headers={'User-Agent': user_agent})
    vo_json_data = json.loads(r.text)

    # print available episode
    print_information("Lecture Nr. | Name | Lecturer | Date")
    counter = 0
    for episode in vo_json_data['episodes']:
        print_information("%2d" % counter + " | " + episode['title'] + " | " + str(episode['createdBy']) + " | " + episode['createdAt'][:-6])
        counter += 1
        link_counter += 1

    # get video selections
    choice = list()
    if download_all:
        # add all available videos to the selected
        choice = list(range(counter))
    else:
        # let user pick videos
        try:
            choice = [int(x) for x in input(
                "Enter numbers of the above lectures you want to download separated by space (e.g. 0 5 12 14)\nJust press enter if you don't want to download anything from this lecture\n"
            ).split()]
        except:
            print()
            print_information("Exiting...")
            sys.exit()
    
    # print the user's choice
    if not choice:
        print_information("No videos selected")
        return # nothing to do anymore
    else:
        print_information("You selected:")
        for item_nr in choice:
            item = vo_json_data['episodes'][item_nr]
            print_information(" - %2d" % item_nr + " " + item['title'] + " " + str(item['createdBy']) + " " + item['createdAt'][:-6])
    print()

    # check whether lecture requires login and get credentials if necessary
    print_information("Protection: " + vo_json_data["protection"], verbose_only=True)
    if vo_json_data["protection"] != "NONE":
        try:
            cookie_jar.update(acquire_login_cookie(vo_json_data["protection"], vo_link))
        except KeyboardInterrupt:
            print()
            print_information("Keyboard interrupt detected, skipping lecture", type='warning')
            return
        
    # collect links and download them
    for item_nr in choice:
        # get link to video metadata json file
        item = vo_json_data['episodes'][item_nr]
        video_info_link = video_info_prefix+item['id']
        
        # download the video metadata file
        # use login-token if provided otherwise make request without cookie
        if(cookie_jar):
            r = requests.get(video_info_link, cookies=cookie_jar, headers={'User-Agent': user_agent})
        else:
            r = requests.get(video_info_link, headers={'User-Agent': user_agent})
        if(r.status_code == 401):
            # the lecture requires a login
            print_information("Received 401 response. The following lecture requires a valid login cookie:", type='error')
            item = vo_json_data['episodes'][item_nr]
            print_information("%2d" % item_nr + " " + item['title'] + " " + str(item['createdBy']) + " " + item['createdAt'][:-6], type='error')
            print_information("Make sure your token is valid. See README.md on how to acquire it.", type='error')
            print()
            continue
        video_json_data = json.loads(r.text)

        
        # put available versions in list for sorting by video quality
        counter = 0
        versions = list()
        print_information("Available versions:", verbose_only=True)
        for vid_version in video_json_data['streams'][0]['sources']['mp4']:
            versions.append((counter, vid_version['res']['w']*vid_version['res']['h']))
            print_information(str(counter) + ": " + "%4d" %vid_version['res']['w'] + "x" + "%4d" %vid_version['res']['h'], verbose_only=True)
            counter += 1
        versions.sort(key=lambda tup: tup[1])
        # Now it's sorted: low -> medium -> high

        # get video src url from json
        video_src_link = video_json_data['streams'][0]['sources']['mp4'][versions[quality_dict[video_quality]][0]]['src']

        # create directory for video if it does not already exist
        directory = directory_prefix + vo_json_data['title'] +"/"
        if not os.path.isdir(directory):
            os.makedirs(directory)
            print_information("This folder was generated: " + directory, verbose_only=True)
        else:
            print_information("This folder already exists: " + directory, verbose_only=True)
        
        # filename is `directory/<video date (YYYY-MM-DD)>-<quality>.mp4`
        file_name = directory+item['createdAt'][:-6]+"-"+video_quality+".mp4"

        # check for print_src flag
        if print_src:
            # print to file if given
            if file_to_print_src_to:
                print_information("Printing " + video_src_link + "to file: "+ file_to_print_src_to, verbose_only=True)
                with open(file_to_print_src_to,"a") as f:
                    f.write(video_src_link+"\n")
            else:
                print_information(video_src_link)
        # otherwise download video
        else:
            downloader(file_name, video_src_link)

def downloader(file_name, video_src_link):
    """Downloads the video and gives progress information"""
    global download_counter
    global skip_counter

    print_information("Video source: " + video_src_link, verbose_only=True)
    
    # check if file already exists
    if os.path.isfile(file_name):
        print_information("download skipped - file already exists: " + file_name.split('/')[-1])
        skip_counter += 1
    # otherwise download it
    else:
        # cf.: https://stackoverflow.com/questions/15644964/python-progress-bar-and-downloads
        with open(file_name+".part", "wb") as f:
            response = requests.get(video_src_link, stream=True)
            total_length = response.headers.get('content-length')   

            print_information("Downloading " + file_name.split('/')[-1] + " (%.2f" % (int(total_length)/1024/1024) + " MiB)")
            
            if total_length is None: # no content length header
                f.write(response.content)
            else:
                # download file and show progress bar
                dl = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = int(50 * dl / total_length)
                    sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)) )    
                    sys.stdout.flush()
        print()
        
        os.rename(file_name+".part", file_name)
        print_information("Downloaded file: " + file_name.split('/')[-1])
        download_counter += 1

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
    print_information(gitlab_issue_page)
    try:
        input("Press enter to open the link in your browser or Ctrl+C to exit.")
        webbrowser.open(gitlab_issue_page)
    except:
        print()
    print_information("Exiting...")
    sys.exit(0)

def apply_args(args):
    """Applies the provided command line arguments
    The following are handled here:
     - verbose
     - bug
     - all
     - quality
     - login-token
    """

    global verbose 
    global download_all
    global video_quality
    global login_token

    global print_src

    #enable verbose for debugging
    verbose = args.verbose
    print_information("Verbose enabled", verbose_only=True)

    # Check if user wants to submit bug report and exit
    if(args.bug == True):
        print_information("If you found a bug you can raise an issue here: ")
        report_bug()
    
    # set global variable according to input
    download_all = args.all
    video_quality = args.quality

    login_token = args.login_token

    # check for printing flag
    if hasattr(args, 'print_src'):
        print_src=True


    # Remove login-token prefix if necessary
    if login_token:
        token_prefix="login-token:"
        if login_token.startswith(token_prefix):
            login_token =login_token[len(token_prefix):]
        print_information("Your login-token: " + login_token, verbose_only=True)

def setup_arg_parser():
    """Sets the parser up"""

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
        "-f", "--file",
        help="A file with links to all the lectures you want to download. Each lecture link should be on a new line. See README.md for details."
    )
    parser.add_argument(
        "-l", "--login-token",
        help="Your login token to download lectures that require a valid NETHZ login. See README.md on how to acquire it."
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
        "-s", "--skip-connection-check",
        action="store_true",
        help="Skip checking whether there's a connection to video.ethz.ch or the internet in general."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print additional debugging information."
    )
    return parser

# ===============================================================
#  __  __           _         
# |  \/  |   __ _  (_)  _ __  
# | |\/| |  / _` | | | | '_ \ 
# | |  | | | (_| | | | | | | |
# |_|  |_|  \__,_| |_| |_| |_|
#
# ===============================================================

# Setup parser and apply commands from input
parser = setup_arg_parser()
args = parser.parse_args()
apply_args(args)

# Connection check
if not args.skip_connection_check:
    check_connection()
else:
    print_information("Connection check skipped.", verbose_only=True)

# Store where to print video source
if print_src and args.print_src:
    file_to_print_src_to = args.print_src

# Collect lecture links
links = list()
if args.file:
    if os.path.isfile(args.file):
        # read provided file    
        with open (args.file, "r") as myfile:
            file_links = myfile.readlines()
        # Strip newlines
        file_links = [x.rstrip('\n') for x in file_links]
        # add links from file to the list of links to look at
        links += file_links
    else:
        print_information("No file with name \"" + args.file +"\" found", type='error')
links += args.lecture_link
        

# Run scraper for every link provided
for item in links:
    print_information("Currently selected: " + item, verbose_only=True)
    if "video.ethz.ch" not in item:
        print_information("Looks like the provided link does not go to 'videos.ethz.ch' and has therefore been skipped. Make sure that it is correct: " + item, type='warning')
    else:    
        vo_scrapper(item)
    print()

# Print summary and exit
print_information(str(link_counter) + " files found, " + str(download_counter) + " downloaded and " + str(skip_counter) + " skipped")
if platform == "win32":
    input('\nEOF') # So Windows users also see the output (apparently)
