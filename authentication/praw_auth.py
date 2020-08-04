import praw
import yaml
import os


def load_configuration():
    conf_file = os.path.join(os.path.dirname(__file__), "../conf/config.yaml")
    with open(conf_file, encoding='utf8') as f:
        configuration = yaml.safe_load(f)
    return configuration


def authenticate():
    config = load_configuration()
    authentication = praw.Reddit(site_name=config['BOT_NAME'], user_agent=config['USER_AGENT'])
    print(f'_Authenticated as {authentication.user.me()}\n')
    return authentication
