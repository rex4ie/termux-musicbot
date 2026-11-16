QUEUE = {}


def add_to_queue(chat_id, songname, link, ref, type, quality):
    QUEUE.setdefault(chat_id, []).append([songname, link, ref, type, quality])
    return len(QUEUE[chat_id]) - 1


def get_queue(chat_id):
    return QUEUE.get(chat_id, 0)


def pop_an_item(chat_id):
    if chat_id in QUEUE:
        QUEUE[chat_id].pop(0)
        return 1
    return 0


def clear_queue(chat_id):
    return 1 if QUEUE.pop(chat_id, None) is not None else 0
