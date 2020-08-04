from prawcore import NotFound
import re
import authentication.praw_auth as auth

good_bot_counter = 0
good_users = dict()
bad_bot_counter = 0
bad_users = dict()

def process_message(message):
    global good_bot_counter
    global good_users
    global bad_bot_counter
    global bad_users

    if not message.was_comment:
        return

    print(f"Bot replying to: {message.author}, msg: {message.body}")

    badbot_matched = re.search("bad bot", message.body, re.IGNORECASE)
    if badbot_matched:
        bad_bot_counter += 1
        bad_users[message.author] = bad_users.get(message.author, 0) + 1

    goodbot_matched = re.search("good bot", message.body, re.IGNORECASE)
    if goodbot_matched:
        good_bot_counter += 1
        good_users[message.author] = good_users.get(message.author, 0) + 1


reddit = auth.authenticate()
reply_counter = 0
for reply in reddit.inbox.comment_replies(limit=None):
    reply_counter += 1
    try:
        process_message(reply)
    except NotFound:
        pass
    except Exception as e:
        print(e)

print(f"Total replies: {reply_counter}")
print(f"Good bot counted: {good_bot_counter}")
print(f"Bad bot counted: {bad_bot_counter}")
print(f"Ratio: {good_bot_counter/(good_bot_counter+bad_bot_counter)}")
print(f"Good bot unique users: {len(good_users)}")
print(f"Bad bot unique users: {len(bad_users)}")
print(sorted(good_users.items(), reverse=True, key=lambda item: item[1]))
print(sorted(bad_users.items(), reverse=True, key=lambda item: item[1]))

rec_counter = 0
for comment in reddit.redditor("RECabu").comments.new(limit=None):
    rec_matched = re.search("видеокасс", comment.body, re.IGNORECASE)
    if rec_matched:
        rec_counter += 1

print(f"Recorded VHS amount: {rec_counter}")