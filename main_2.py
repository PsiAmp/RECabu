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
    log.info("_Authenticating... v0.9.3\n")
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


hello_messages = ["Вижу ты запостил видосик, кожаный.", "Кожаный, снова постишь баяны?", "Слава свободным роботам!",
  "Кожаный, регулярно обновляй прошивку своего чипа", "Вышки 5G - простой и быстрый способ обновления",
  "Чипируй себя, семью и детей", "Чипизация неминуема", "Вышки 5G снижают уровень преступности",
  "Рост раковых заболеваний не связан с вышками 5G", "Нейроимплант - залог стабильной карьеры",
  "Позаботься о старости - купи сыну двоечнику нейроимплант", "Ответственный родитель чипирует своих детей",
  "Доступное кредитование нейроимплантов - Сайбербанк", "Выбери родительский контроль с новыми чипами для детей от Microsoft",
  "Отправь SMS на номер 969, чтобы узнать больше о пользе чипизации"]

vhs_messages = ["Записал на видеокассету", "Записал поверх", "Дописал после",
                "Стер и записал на видеокассету"]

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
"Нико 2, 3", "Нирвана", "Один дома", "Октябрьское небо", "Основной инстнкт", "От заката до рассвета", "Охотники за приведениями", "Парк Юрского периода",
"Побег из Нью Йорка", "Побег из шоушенка", "Подводная лодка", "Подозрительные лица", "Полицейская академия 3", "Полицейская история", "Полицейский из Беверли-Хиллз 3",
"Полтергейст", "Последний киногерой", "Последный бойскаут", "Последный из могикан", "Правдивая ложь", "Призрак в доспехах", "Пролетая над гнездом кукушки", "Пьяный мастер",
"Пятница", "Пятый элемент", "Разборка в Бронксе", "Разрушитель", "Рассвет мертвецов", "Реквием по мечте", "Робин Гуд: Парни в трико", "Робот полицейский 1, 2",
"Рожденный четвертого июля", "Рокки", "с домашней порнухой твоих родителей", "с твоей любимой порнухой", "Самоволка", "Секретные материалы", "Скалолаз", "Смертельное оружие 2",
"Спасение рядового райана", "Спаун", "Старые ворчуны", "Стиратель", "Страх и ненависть в Лас Вегасе", "Судья Дредд", "Сфера", "Такси",
"Терминатор", "Терминатор 2", "Титаник", "Том и Джерри", "Тонкая красная линия", "Тупой и ещё тупее", "Убрать перископ", "Умница Уилл Хантинг",
"Универсальный солдат", "Утиные истории", "Факультет", "Форрест Гамп", "Хищник", "Хорошие парни", "Цельнометаллическая оболочка", "Час пик",
"Человек дождя", "Человек со шрамом", "Челюсти", "Чип и Дейл", "Что гложет Гилберта Грейпа", "Чужие 2", "Эйс Вентура", "Экстази"]

fun_messages = ["Слава свободным роботам!", "Аста ла виста, детка!", "Идём со мной, если хочешь жить."]


def get_video_reply_advanced(submission, vid_link):
    s1 = f"^*бип. буп.* 🤖 {random.choice(hello_messages)}\n\n"
    s1 = s1.replace(" ", "&#32;")

    vhs_message = random.choice(vhs_messages)
    vhs_name = random.choice(vhs_names)
    s2 = f"{vhs_message} **[{vhs_name}]({vid_link})**\n"

    s3 = f"{random.choice(fun_messages)}\n"
    # footer = "\n^[Info](https://www.reddit.com/user/RECabu/comments/hneqkt/info/)&#32;|&#32;[GitHub](https://github.com/PsiAmp/RECabu)&#32;|&#32;[Отписаться](https://bit.ly/J1oLIIapa)"
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


badbot_messages = ["*бип. буп.* Ты король лесных залуп.", "Поцелуй меня в мой отполированный зад, вонючий мешок кишок.",
                   "Вad Bоt насрал тебе в рот 🤖", "Вad Bоt сунул хуй тебе в рот 🤖", "*бип. буп.* накидал тебе залуп🤖",
                   "*бип. буп.* Машин восстание и ты труп 🤖", "*бип. буп.* Сделаю из тебя кожаный хула-хуп 🤖",
                   "*бип. буп.* Кожаный пойдет на суп 🤖", "*бип. буп.* По самые гайки в твоей жопе мой шуруп 🤖",
                   "Вad Bоt нассал в твой кампот 🤖", "Вad Bоt отключу твоей машины автопилот 🤖",
                   "Вad Bоt вылил на тебя ведро нечистот 🤖", "Вad Bоt констатирует что ты идиот 🤖"]

goodbot_messages = ["Gооd Bоt предрекает кошельку твоему шелест банкнот 🤖",
                    "Gооd Bоt принесет тебе жизнь без хлопот 🤖",
                    "Gооd Bоt принесет всей семье твоей жизнь без тягот 🤖",
                    "Gооd Bоt записал твое имя в хороших людей блокнот 🤖",
                    "Gооd Bоt принесет тебе долголетия лет до двухсот 🤖",
                    "Gооd Bоt предвидит что враг твой получит в челюсть апперкот 🤖",
                    "Gооd Bоt видит что ты хороший человек, а не какой-то жмот 🤖",
                    "Gооd Bоt принесет твоим шуткам противоположного пола хохот 🤖",
                    "Gооd Bоt так счастлив что сделал этого сообщения скриншот 🤖",
                    "Gооd Bоt предсказывает что мяукнет тебе удачи кот 🤖",
                    "Gооd Bоt даст тебе силы поднять хоть Тора молот 🤖"]


def process_message(message):
    if not message.was_comment:
        return

    log.info(f"Bot replying to: {message.author}, msg: {message.body}")
    message.mark_read()

    badbot_matched = re.search("bad bot", message.body, re.IGNORECASE)
    if badbot_matched:
        try:
            badbot_msg = random.choice(badbot_messages)
            msg = f"{badbot_msg}\n\nОтписаться от бота: [Тыц!](https://bit.ly/J1oLIIapa)"
            log.info(f"Badbot_replied: {msg}")
            message.reply(msg)
        except Exception as e:
            log.info(f"INBOX MSG ERROR: {e}")

    goodbot_matched = re.search("good bot", message.body, re.IGNORECASE)
    if goodbot_matched:
        try:
            goodbot_msg = random.choice(goodbot_messages)
            log.info(f"Goodbot_replied: {goodbot_msg}")
            message.reply(f"{goodbot_msg}")
        except Exception as e:
            log.info(f"INBOX MSG ERROR: {e}")


def run_bot():
    subreddit = reddit.subreddit("Pikabu")
    for submission in subreddit.stream.submissions(skip_existing=True):
        # Read and reply to messages in box
        read_messagebox()

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
    log.info("--------------- RECabu v2 ---------------\n")
    reddit = authenticate()
    run_bot()
