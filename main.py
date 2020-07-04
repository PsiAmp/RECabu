import re
import praw
import requests
import yaml
import os
import urllib.parse
from urllib.error import HTTPError, URLError
from urllib.request import Request


def authenticate():
    print('Authenticating...\n')
    authentication = praw.Reddit(site_name=config['BOT_NAME'], user_agent=config['USER_AGENT'])
    print(f'Authenticated as {authentication.user.me()}\n')
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


def is_comment_summoning(comment):
    body = str(comment.body)
    rec_matched = re.search("rec", body, re.IGNORECASE)
    vreddit_matched = re.search("vredditdownloader", body, re.IGNORECASE)
    return (rec_matched or vreddit_matched) and len(body) <= 20


def is_video_submission(comment):
    return "v.redd.it" in comment.submission.url


def run_bot():
    subreddit = reddit.subreddit("GamingTrailers")
    for comment in subreddit.stream.comments():

        # Check if comment is summoning RECabu bot
        if is_comment_summoning(comment):
            print(f"Summonning comment: {comment.body}")

            # Check if summoning comment belongs to a valid video submission
            if is_video_submission(comment):
                print("Video submission is valid")

                # Get a video link from RedditTube
                vid_link = upload_via_reddittube(f"https://www.reddit.com{comment.submission.permalink}")

                # Check if a link is valid
                if is_link_valid(vid_link):
                    print(f"Video link from reddittube: {vid_link}")
                    try:
                        print("___Test: Записал")
                        # Reply to summoner with a link
                        # comment.reply("[Записал на видеокассету](" + vid_link + ")")
                    except Exception as e:
                        print(e)
                else:
                    print("not a valid link: " + vid_link)


if __name__ == '__main__':
    config = load_configuration()
    reddit = authenticate()
    run_bot()
