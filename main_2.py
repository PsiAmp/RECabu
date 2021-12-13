import strings.message_strings as strings
import random
import argparse
import time
import re
import praw
from prawcore import NotFound
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
log = logging.getLogger('RECabu_logger')


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
    log.info("_Authenticating...")
    authentication = praw.Reddit(site_name=config['BOT_NAME'], user_agent=config['USER_AGENT'])
    log.info(f'_Authenticated as {authentication.user.me()}')
    return authentication


def load_configuration():
    conf_file = os.path.join(os.path.dirname(__file__), "conf/config.yaml")
    with open(conf_file, encoding='utf8') as f:
        configuration = yaml.safe_load(f)
    return configuration


def upload_reddittube_fast(link):
    # log.info("Linking directly to https://reddit.tube")
    return link.replace(".com", ".tube")


def upload_reddittube_slow(link):
    site_url = "https://reddit.tube/parse"
    response = requests.get(site_url, params={
        'url': link
    })
    response_json = response.json()
    return response_json['share_url']


def upload_via_reddittube(link):
    # try:
    #     uploaded_url = upload_reddittube_slow(link)
    #     if is_link_valid(uploaded_url):
    #         return uploaded_url
    # except Exception as e:
    #     log.info(e)
    return upload_reddittube_fast(link)


# Get a link to rediRECt
def upload_via_redirect(post_id):
    return f"http://ec2-3-142-73-12.us-east-2.compute.amazonaws.com:8090/recabu/{post_id}/"


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
        # log.info(f"Gfy link: {gfy_link}")
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


def get_video_reply_advanced(submission, vid_link):
    s1 = f"^*бип.&#32;буп.*&#32;🤖\n\n"

    vhs_message = random.choice(strings.vhs_messages)
    vhs_name = random.choice(strings.vhs_names)
    s2 = f"{vhs_message} **[{vhs_name}]({vid_link})**\n"

    footer = "\n^[Info](https://www.reddit.com/user/RECabu/comments/hneqkt/info/)&#32;|&#32;[GitHub](https://github.com/PsiAmp/RECabu)"
    return s2 + footer


def reply(submission, vid_link):
    # log.info(f"Video link : {vid_link}")
    try:
        # Reply to submission
        reply_text = get_video_reply_advanced(submission, vid_link)

        if not is_debug:
            submission.reply(reply_text)

        # log.info(f"Replied: {reply_text}")
        if is_debug:
            print(f"Replied: {reply_text}")
    except Exception as e:
        log.info(e)


def read_messagebox():
    inbox = list(reddit.inbox.unread(limit=config['INBOX_LIMIT']))
    inbox.reverse()
    for message in inbox:
        try:
            process_message(message)
        except NotFound:
            pass
        except Exception as e:
            print(e)
            log.info(e)


def process_message(message):
    if not message.was_comment:
        return

    # log.info(f"Bot replying to: {message.author}, msg: {message.body}")

    badbot_matched = re.search("bad bot", message.body, re.IGNORECASE)
    if badbot_matched:
        try:
            message.mark_read()
            # msg = f"{badbot_msg}\n\nОтписаться от бота: [Тыц!](https://www.youtube.com/watch?v=dQw4w9WgXcQ)"
            # log.info(f"Badbot_replied: {msg}")
            # message.reply(msg)
            # message.reply(random.choice(strings.otzyv_messages))
        except Exception as e:
            log.info(f"INBOX MSG ERROR: {e}")

    goodbot_matched = re.search("good bot", message.body, re.IGNORECASE)
    if goodbot_matched:
        try:
            message.mark_read()
            # goodbot_msg = random.choice(goodbot_messages)
            # log.info(f"Goodbot_replied: {goodbot_msg}")
            # message.reply(f"{goodbot_msg}")
        except Exception as e:
            log.info(f"INBOX MSG ERROR: {e}")


def run_bot():
    subreddit = reddit.subreddit("Pikabu")
    posted_submission_ids = set()

    for submission in subreddit.stream.submissions(skip_existing=True):
        # Read and reply to messages in box
        read_messagebox()

        # Check if post is already submitted to avoid double comments in the same post that sometimes occur during
        # Reddit servers disturbances
        # Skip adding a reply if submission id is already in the set
        if submission.id in posted_submission_ids:
            continue

        # Put submission id in the set
        posted_submission_ids.add(submission.id)

        # Check if summoning comment belongs to a valid video submission
        if is_reddit_video_submission(submission):
            # log.info(f"Post is a Reddit video submission: https://www.reddit.com{submission.permalink}")

            # Get a video link from RedditTube
            vid_link = upload_via_reddittube(f"https://www.reddit.com/r/Pikabu/comments/{submission.id}/")

            # Get a link to rediRECt
            vid_link = upload_via_redirect(submission.id)

            # Post reply
            reply(submission, vid_link)
        elif is_gfycat_video_submission(submission):
            # log.info(f"Post is a GfyCat video submission: {submission.url}")
            gfy_vid_link = get_gfycat_video_link(submission.url)
            if gfy_vid_link:
                reply(submission, gfy_vid_link)


if __name__ == '__main__':
    config = load_configuration()
    init_logger()
    log.info("--------------- RECabu_v2.1 ---------------")
    reddit = authenticate()
    run_bot()
