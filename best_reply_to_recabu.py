import main_2
from queue import PriorityQueue
import heapq


def get_replies(comment, pq, size):
    comment.refresh()
    if comment.replies:
        for reply in comment.replies:
            if reply:
                reply.refresh()
                pq.append((reply.score, reply))
                get_replies(reply, pq, size)


if __name__ == '__main__':
    main_2.config = main_2.load_configuration()
    reddit = main_2.authenticate()
    recabu = reddit.redditor("RECabu")

    top_comments = []

    for comment in recabu.comments.new(limit=None):
        get_replies(comment, top_comments, 20)

    while comment in top_comments:
        print(comment[0], ':', comment[1].body)

    sorted(top_comments, key=lambda tup: tup[0], reverse=True)