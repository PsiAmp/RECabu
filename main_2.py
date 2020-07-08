import argparse
import time
import re
import praw
import requests
import yaml
import os
import logging
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler
import urllib.parse
from urllib.error import HTTPError, URLError
from urllib.request import Request

# Store startup time
start_time = time.time()

# Is assigned to a platform logger
log = logging.getLogger('cloudLogger')


# Parsing command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-debug', action="store_true", default=False)
args, unknown = parser.parse_known_args()
is_debug = args.debug


# Init logger that will be visible in Global scope
def init_logger():
    log.setLevel(logging.INFO)
    if not is_debug:
        client = google.cloud.logging.Client()
        handler = CloudLoggingHandler(client)
        log.addHandler(handler)


def authenticate():
    log.info("_Authenticating... v0.9.0\n")
    authentication = praw.Reddit(site_name=config['BOT_NAME'], user_agent=config['USER_AGENT'])
    log.info(f'_Authenticated as {authentication.user.me()}\n')
    print(f'_Authenticated as {authentication.user.me()}\n')
    return authentication


def load_configuration():
    conf_file = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(conf_file, encoding='utf8') as f:
        configuration = yaml.safe_load(f)
    return configuration


def upload_via_reddittube(link):
    site_url = "https://reddit.tube/parse"
    response = requests.get(site_url, params={
        'url': link
    })
    response_json = response.json()
    return response_json['share_url']


def is_link_valid(link):
    # Check if download is valid without downloading
    if "reddit.tube" in link:
        if requests.head(link).ok:
            return True
        return False

    try:
        status_code = urllib.request.urlopen(link, timeout=2).getcode()
        return status_code == 200
    except (HTTPError, URLError, ValueError):
        return False


def get_gfycat_video_link(url):
    # gfy_url = 'https://gfycat.com/quarterlymintyblueshark'
    prefix = 'property="og:video" content="'
    suffix = '-mobile.mp4'
    prefix_link = 'https://thumbs.gfycat.com/'

    try:
        # Get response
        response = requests.get(url)
        # Get html
        resp_text = response.text
        # Find url marker
        start = resp_text.find(prefix)
        # Find suffix
        end = resp_text.find(suffix, start)
    except Exception as e:
        log.info(e)

    if start and end:
        gfy_link = resp_text[start + len(prefix):end + len(suffix)]
        log.info(f"Gfy link: {gfy_link}")
        # Validate link
        if gfy_link.startswith(prefix_link) and gfy_link.endswith(suffix):
            return gfy_link
        else:
            log.info("Validation didn't pass")
    return False


def is_reddit_video_submission(submission):
    return "v.redd.it" in submission.url


def is_gfycat_video_submission(submission):
    return str(submission.url).startswith('https://gfycat.com')


def get_video_reply(submission, vid_link):
    if submission.author == "PsiAmp":
        return f"[Записал на видеокассету]({vid_link}), мастер PsiAmp."
    return f"Вжух! [Записал на видеокассету]({vid_link})"


def reply(submission, vid_link):
    log.info(f"Video link from reddittube: {vid_link}")
    try:
        # Reply to summoner with a link
        reply_text = get_video_reply(submission, vid_link)

        if not is_debug:
            submission.reply(reply_text)

        log.info(f"Replied: {reply_text}")
        if is_debug:
            print(f"Replied: {reply_text}")
    except Exception as e:
        log.info(e)


def run_bot():
    subreddit = reddit.subreddit("Pikabu")
    for submission in subreddit.stream.submissions(skip_existing=True):

        # Check if summoning comment belongs to a valid video submission
        if is_reddit_video_submission(submission):
            log.info("Post is a Reddit video submission")

            # Get a video link from RedditTube
            vid_link = upload_via_reddittube(f"https://www.reddit.com{submission.permalink}")

            # Check if a link is valid
            if is_link_valid(vid_link):
                reply(submission, vid_link)
            else:
                log.info("not a valid link: " + vid_link)
        elif is_gfycat_video_submission(submission):
            log.info(f"Post is a GfyCat video submission: {submission.url}")
            gfy_vid_link = get_gfycat_video_link(submission.url)
            if gfy_vid_link:
                reply(submission, gfy_vid_link)


if __name__ == '__main__':
    config = load_configuration()
    init_logger()
    reddit = authenticate()
    run_bot()
