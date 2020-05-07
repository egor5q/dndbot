import os
from abc import ABC

from pymongo import MongoClient

# вообще-то, это не совсем конфиг. Сюда будем всякое полезное складывать. Это, скорее, файл с утилитами

dndbot_token = os.environ['dnd']
mongo_client = MongoClient(os.environ['database'])

pasyuk_id = 441399484
senderman_id = 94197300
admins = (pasyuk_id, senderman_id)


# абстрактный класс, который можно использовать как хранилище для сообщений "собрать пчелу/вайфу"
class CollectableMessage(ABC):

    def __init__(self, chat_id, amount, message_id):
        self.chat_id = chat_id
        self.amount = amount  # кол-во оставшихся пчел/вайфу в сообщении
        self.message_id = message_id
        self.users = set()  # кто уже забрал
        self.button_id = str(chat_id) + ' ' + str(message_id)

    # используем этот метод чтобы закинуть данный класс в словарь с помощью dict.update()
    def to_dict(self):
        return {
            self.button_id: self
        }


# сделать строку безопасной для HTML парсмода в сообщениях
def make_safe_html(string):
    string = str(string)
    return string.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")


# same as above, только для маркдауна
def make_safe_markdown(string):
    string = str(string)
    return string.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
