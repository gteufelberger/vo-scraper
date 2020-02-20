# vo-scraper

A python script for ETH students to download lecture videos from [video.ethz.ch](https://video.ethz.ch/).

## Requirements:
 * `requests`

Install with:

    pip3 install requests

## Setup
Download the file

    git clone https://gitlab.ethz.ch/tgeorg/vo-scraper.git

and run with

    python3 vo-scraper.py

or

    chmod +x vo-scraper.py
    ./vo-scraper.py



# FAQ

### Q: How do I use it?

#### A:

    python3 vo-scraper.py --help


### Q: How do I pass a file with links to multiple lectures?

#### A: Use `--file <filename>` 

The file should have a link on each new line. It should look something like this:

    https://video.ethz.ch/lectures/d-infk/<year>/<spring/autumn>/XXX-XXXX-XXL.html
    https://video.ethz.ch/lectures/d-infk/<year>/<spring/autumn>/XXX-XXXX-XXL.html
    ...

### <a name="how_it_works"></a> Q: How does it work?

#### A: Like so:

Each lecture on [video.ethz.ch](https://video.ethz.ch/) has a JSON file with metadata associated with it.

So for example

    https://video.ethz.ch/lectures/d-infk/2019/spring/252-0028-00L.html

has its JSON file under:

    https://video.ethz.ch/lectures/d-infk/2019/spring/252-0028-00L.series-metadata.json

This JSON file contains a list of all "episodes" where the ids of all the videos of the lecture are located.

Using those ids we can access another JSON file with the video's metadata under

    https://video.ethz.ch/.episode-video.json?recordId=<ID>

Example:

    https://video.ethz.ch/.episode-video.json?recordId=3f6dee77-396c-4e2e-a312-a41a457b319f

This file contains links to all available video streams (usually 1080p, 720p, and 360p). Note that if a lecture requires a login, this file will only be accessible if you a cookie with a valid login-token!

The link to the video stream looks something like this:

    https://oc-vp-dist-downloads.ethz.ch/mh_default_org/oaipmh-mmp/<video id>/<video src id?>/presentation_XXXXXXXX_XXXX_XXXX_XXXX_XXXXXXXXXXXX.mp4

Example:

    https://oc-vp-dist-downloads.ethz.ch/mh_default_org/oaipmh-mmp/3f6dee77-396c-4e2e-a312-a41a457b319f/2bd93636-e95d-4552-8722-332a95e1a0a6/presentation_c6539ed0_1af9_490d_aec0_a67688dad755.mp4

So what the vo-scraper does is getting the list of episodes from the lecture's metadata and then acquiring the links to the videos selected by the user by accessing the videos' JSON files. Afterwards it downloads the videos behind the links.


### Q: It doesn't work for my lecture. What can I do to fix it?

#### A: Follow these steps:
1. Make sure you have connection to [video.ethz.ch](https://video.ethz.ch/). The scraper should let you know when there's no connection.
2. Try running it again. Sometimes random issues can throw it off.
3. Make sure that you haven't just forgotten to add a login-token on a lecture that requires a valid login. Also make sure the token is still up to date.
4. Check whether other lectures still work. Maybe the site was updated which broke the scraper.
5. Enable the debug flag with `-v` and see whether any of the additional information now provided is helpful.
6. Check "[How does it work?](#how_it_works)" and see whether you can manually reach the video in your browser following the steps described there.
7. After having tried all that without success, feel free to open up a new issue. Make sure to explain what you have tried and what the results were. There is no guarantee I will respond within reasonable time as I'm a busy student myself. If you can fix the issue yourself, feel free to open a merge request with the fix.


### Q: Can you fix *X*? Can you implement feature *Y*?

#### A: Feel free open a merge request with the requested change implemented. If I like it, I'll merge it.

***

Loosely based on https://gitlab.ethz.ch/dominik/infk-vorlesungsscraper
