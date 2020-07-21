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
    log.info("_Authenticating...")
    authentication = praw.Reddit(site_name=config['BOT_NAME'], user_agent=config['USER_AGENT'])
    log.info(f'_Authenticated as {authentication.user.me()}')
    return authentication


def load_configuration():
    conf_file = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(conf_file, encoding='utf8') as f:
        configuration = yaml.safe_load(f)
    return configuration


def upload_reddittube_fast(link):
    log.info("Linking directly to https://reddit.tube")
    return link.replace(".com", ".tube")


def upload_reddittube_slow(link):
    site_url = "https://reddit.tube/parse"
    response = requests.get(site_url, params={
        'url': link
    })
    response_json = response.json()
    return response_json['share_url']


def upload_via_reddittube(link):
    try:
        uploaded_url = upload_reddittube_slow(link)
        if is_link_valid(uploaded_url):
            return uploaded_url
    except Exception as e:
        log.info(e)

    return upload_reddittube_fast(link)


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


vhs_messages = ["Записал на видеокассету"]

vhs_names = ["Баяны", "Бегущий по лезвию бритвы", "Блейд", "Бэтмен возвращается", "ВК-180", "Водный мир", "Вспомнить всё", "Вспомнить всё",
"Газонокосильщик", "Голый пистолет", "Горец", "Грязные танцы", "12 обезьян", "9 1/2 недель", "Адвокат дьявола", "Акира",
"Аладдин", "Американская красотка", "Американский психопат", "Аполлон 13", "Армагеддон", "Без лица", "Бездна", "Бешеные псы",
"Бойцовский клуб", "Ведьмина служба доставки", "Внутренний космос", "Возвращение живых мертвецов", "Горячие головы", "Гремлины", "Двойной удар", "Двухсотлетний человек",
"День Независимости (боевик)", "День Сурка", "Дерсу Узала", "Джонни Мнемоник", "Дорогая, я уменьшил детей", "Доспехи бога", "Дракула", "Дрожь земли",
"Запах женщины", "Зарубежные клипы", "Звездные войны V", "Звездные врата", "Звездный десант", "Звёздный десант", "Зеленая миля", "Зловещие мертвецы",
"Знакомтесь, Джо Блэк", "Золотые баяны", "Игра", "Индиана Джонс", "История игрушек", "Каспер", "Кин-дза-дза", "Контакт",
"Король лев", "Космобольцы", "Кошмар на улице Вязов", "Кошмар на улице Вязов 5", "Крепкий орешек", "Крестный отец", "Крестный отец 3", "Куда приводят мечты",
"Лепрекон 5: Сосед", "Майор Пэйн", "Маска", "Митечка - выпускной", "Мишки Гамми", "Мой кузен Винни", "Мой сосед Тоторо", "Молчание ягнят",
"Мортал Комбат", "Мумия", "Муха", "На игле", "Навсикая из Долины ветров", "Назад в будущее II", "Не грози Южному централу, попивая сок у себя в квартале", "Нечто",
"Нико 2, 3", "Нирвана", "Один дома", "Октябрьское небо", "Основной инстинкт", "От заката до рассвета", "Охотники за приведениями", "Парк Юрского периода",
"Побег из Нью Йорка", "Побег из шоушенка", "Подводная лодка", "Подозрительные лица", "Полицейская академия 3", "Полицейская история", "Полицейский из Беверли-Хиллз 3",
"Полтергейст", "Последний киногерой", "Последный бойскаут", "Последный из могикан", "Правдивая ложь", "Призрак в доспехах", "Пролетая над гнездом кукушки", "Пьяный мастер",
"Пятница", "Пятый элемент", "Разборка в Бронксе", "Разрушитель", "Рассвет мертвецов", "Реквием по мечте", "Робин Гуд: Парни в трико", "Робот полицейский 1, 2",
"Рожденный четвертого июля", "Рокки", "c порнухой твоего бати", "с домашней порнухой твоих родителей", "с твоей любимой порнухой",
"Самоволка", "Секретные материалы", "Скалолаз", "Смертельное оружие 2",
"Спасение рядового райана", "Спаун", "Старые ворчуны", "Стиратель", "Страх и ненависть в Лас Вегасе", "Судья Дредд", "Сфера", "Такси",
"Терминатор", "Терминатор 2", "Титаник", "Том и Джерри", "Тонкая красная линия", "Тупой и ещё тупее", "Убрать перископ", "Умница Уилл Хантинг",
"Универсальный солдат", "Утиные истории", "Факультет", "Форрест Гамп", "Хищник", "Хорошие парни", "Цельнометаллическая оболочка", "Час пик",
"Человек дождя", "Человек со шрамом", "Челюсти", "Чип и Дейл", "Что гложет Гилберта Грейпа", "Чужие 2", "Эйс Вентура", "Экстази"]


def get_video_reply_advanced(submission, vid_link):
    s1 = f"^*бип.&#32;буп.*&#32;🤖\n\n"

    vhs_message = random.choice(vhs_messages)
    vhs_name = random.choice(vhs_names)
    s2 = f"{vhs_message} **[{vhs_name}]({vid_link})**\n"

    footer = "\n^[Info](https://www.reddit.com/user/RECabu/comments/hneqkt/info/)&#32;|&#32;[GitHub](https://github.com/PsiAmp/RECabu)"
    return s1 + s2 + footer


def reply(submission, vid_link):
    log.info(f"Video link from reddittube: {vid_link}")
    try:
        # Reply to summoner with a link
        reply_text = get_video_reply_advanced(submission, vid_link)

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
            log.info(f"Post is a Reddit video submission: https://www.reddit.com{submission.permalink}")

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
    log.info("--------------- RECabu_v2.1 ---------------")
    reddit = authenticate()
    run_bot()
