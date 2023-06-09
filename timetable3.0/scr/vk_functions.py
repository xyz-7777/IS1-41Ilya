import os

from vk_api import vk_api
import json
import random
from time import sleep

token = "TOKEN"

vk = vk_api.VkApi(token=token)
vk_ = vk.get_api()

def get_surname_by_id(peer_id):
    try:
        user = vk.method("users.get", {"user_ids": peer_id})
        return user[0]['last_name']
    except:
        return ''


def msg_keyboard(text, peer_id, keyboard):
    vk.method("messages.send",
              {"peer_id": peer_id, "message": text, "keyboard": keyboard, "random_id": random.randint(1, 2147483647)})


def msg(text, peer_id, attachment=None):
    vk.method("messages.send", {"peer_id": peer_id, "attachment": attachment, "message": text,
                                "random_id": random.randint(1, 2147483647)})


def create_button(text, color):
    return [{"action": {"type": "text", "label": text}, "color": color}]


def create_keyboard(texts, back):
    keyboard_buttons = {"one_time": False, "buttons": []}
    for text in texts:
        keyboard_buttons["buttons"].append(create_button(text, "positive"))
    if back:
        keyboard_buttons["buttons"].append(create_button("Назад", "negative"))
    keyboard_json = json.dumps(keyboard_buttons)
    return keyboard_json


def create_button_dict(text, color):
    return {"action": {"type": "text", "label": text}, "color": color}


keyboard_main = json.dumps({
    "one_time": False,
    "buttons": [
        [create_button_dict("Расписание", "positive")],
        [create_button_dict("Предыдущее", "primary"), create_button_dict("Следующее", "primary")],
        [create_button_dict("Замены", "negative"), create_button_dict("Команды", "secondary")],
    ]})


def create_commands_keyboard(person_info):
    keyboard = json.dumps({
        "one_time": False,
        "buttons": [
            [create_button_dict("Числитель", "primary"), create_button_dict("Знаменатель", "primary")],
            [create_button_dict("Расписание звонков", "positive"), create_button_dict("Поддержка", "secondary")],
            [create_button_dict("Отображать начало пары",
                                "positive" if person_info.get('show_start_pair') else "negative")],
            # , create_button_dict("Рассылка", "primary") create_button_dict("Замены на сайте", "positive"),
            [create_button_dict("Изменить группу", "primary")],
            [create_button_dict("Назад", "negative")],
        ]})
    return keyboard


def get_conversations():
    return vk.method("messages.getConversations",
                     {"offset": 0, "count": 100, "filter": "unread", "random_id": random.randint(1, 2147483647)})


def markAsRead(peer_id):
    vk.method("messages.markAsRead", {"peer_id": peer_id, "random_id": random.randint(1, 2147483647)})

from functools import wraps
import psycopg2, psycopg2.extensions


def retry(fn):
    @wraps(fn)
    def wrapper(*args, **kw):
        cls = args[0]
        for x in range(cls._reconnectTries):
            print(x, cls._reconnectTries)
            try:
                return fn(*args, **kw)
            except (psycopg2.InterfaceError, psycopg2.OperationalError) as e:
                print("\nDatabase Connection [InterfaceError or OperationalError]")
                print("Idle for %s seconds" % (cls._reconnectIdle))
                sleep(cls._reconnectIdle)
                cls._connect()

    return wrapper


class TimetableDatabase:
    _reconnectTries = 30
    _reconnectIdle = 5 # wait seconds before retying

    def __init__(self):
        self.my_connection = None
        self.my_cursor = None
        self.DATABASE_URL = "URL"
        self._connect()
        self.execute_is_active = False

    def _connect(self):
        self.my_connection = psycopg2.connect(self.DATABASE_URL, sslmode='require')
        self.my_cursor = self.my_connection.cursor()
        self.my_connection.autocommit = True

    def do_execute(self, data):
        while self.execute_is_active:
            pass
        self.execute_is_active = True
        with self.my_connection:
            self.my_cursor.execute(data)
            self.execute_is_active = False

    def change_user(self, vk_id, role='', teacher_name='', department='', change_groups='', change_group='', sending='', sending_time='',
                    show_start_pair=''):
        command = f'UPDATE timetable SET '

        if role != '':
            if role is None:
                command += f"role=NULL,"
            else:
                command += f"role='{role}',"
        if teacher_name != '':
            if teacher_name is None:
                command += f"teacher_name=NULL,"
            else:
                command += f"teacher_name='{teacher_name}',"
        if department != '':
            if department is None:
                command += f"department=NULL,"
            else:
                command += f"department='{department}',"
        if change_groups != '':
            if change_groups is None:
                command += f"change_groups=NULL,"
            else:
                command += f"change_groups='{change_groups}',"
        if change_group != '':
            if change_group is None:
                command += f"change_group=NULL,"
            else:
                command += f"change_group='{change_group}',"
        if sending != '':
            if sending is None:
                command += f"sending=NULL,"
            else:
                command += f"sending={sending},"
        if sending_time != '':
            if show_start_pair is None:
                command += f"show_start_pair=NULL,"
            else:
                command += f"sending_time='{sending_time}',"
        if show_start_pair != '':
            if sending_time is None:
                command += f"sending_time=NULL,"
            else:
                command += f"show_start_pair='{show_start_pair}',"

        command = command[:-1] + f" WHERE vk_id={vk_id};"
        print(command)
        self.do_execute(command)

    def del_user(self, vk_id):
        print(f'[DEL] {vk_id}')
        self.do_execute(
            f'UPDATE timetable SET department=NULL, change_groups=NULL, '
            f'change_group=NULL, role=NULL, teacher_name=NULL WHERE vk_id={vk_id};')

    def add_user(self, vk_id):
        print(f'[ADD] {vk_id}')
        self.do_execute(f"INSERT INTO timetable(vk_id, sending, sending_time, show_start_pair, role) "
                        f"VALUES({vk_id}, 0, '12:00', TRUE, NULL);")

    def get_user(self, vk_id):
        self.do_execute(f'SELECT * FROM timetable WHERE vk_id={vk_id};')
        if not self.my_cursor:
            return None
        for row in self.my_cursor:
            print(row)
            if row:
                # print(row)
                return {
                    "sending": row[2],
                    "sending_time": row[3],
                    "department": row[4],
                    "change_groups": row[5],
                    "change_group": row[6],
                    "show_start_pair": row[7],
                    "role": row[8],
                    "teacher_name": row[9],
                }
            return None

    def print_table(self):
        self.do_execute('SELECT * FROM timetable;')
        all_users = {}

        for row in self.my_cursor:
            all_users[row[1]] = {
                "sending": row[2],
                "sending_time": row[3],
                "department": row[4],
                "change_groups": row[5],
                "change_group": row[6],
                "show_start_pair": row[7],
                "role": row[8],
                "teacher_name": row[9]
            }
        return all_users

    def __del__(self):
        # Maybe there is a connection but no cursor, whatever close silently!
        for c in (self.my_cursor, self.my_connection):
            try:
                c.close()
            except:
                pass


CALL_SCHEDULE = {
    'ОИТУП': {
        "workweek": {
            0: ["7:40", "8:50"],
            1: ["9:00", "10:30"],
            2: ["10:40", "12:10"],
            3: ["12:55", "14:25"],
            4: ["14:40", "16:10"],
            5: ["16:40", "18:10"],
            6: ["18:20", "19:50"],
            7: ["20:00", "21:30"],
        },
        "saturday": {
            0: ["7:40", "8:50"],
            1: ["9:00", "10:30"],
            2: ["10:40", "12:10"],
            3: ["12:55", "14:25"],
            4: ["14:35", "16:05"],
            5: ["16:15", "17:45"],
            6: ["18:20", "19:50"],
            7: ["20:00", "21:30"],
        }
    },
    'ОЭП': {
        "workweek": {
            0: ["7:40", "8:50"],
            1: ["9:00", "10:30"],
            2: ["10:40", "12:30"],
            3: ["13:00", "14:30"],
            4: ["14:40", "16:10"],
            5: ["16:40", "18:10"],
            6: ["18:20", "19:50"],
            7: ["20:00", "21:30"]
        },
        "saturday": {
            0: ["7:40", "8:50"],
            1: ["9:00", "10:30"],
            2: ["10:40", "12:30"],
            3: ["13:00", "14:30"],
            4: ["14:40", "16:10"],
            5: ["16:20", "17:50"],
            6: ["18:20", "19:50"],
            7: ["20:00", "21:30"]
        },
    },
    'ММО': {
        "workweek": {
            0: ["7:40", "8:50"],
            1: ["9:00", "10:30"],
            2: ["10:40", "12:10"],
            3: ["12:55", "14:25"],
            4: ["14:40", "16:10"],
            5: ["16:40", "18:10"],
            6: ["18:20", "19:50"],
            7: ["20:00", "21:30"]
        },
        "saturday": {
            0: ["7:40", "8:50"],
            1: ["9:00", "10:30"],
            2: ["10:40", "12:10"],
            3: ["12:55", "14:25"],
            4: ["14:35", "16:05"],
            5: ["16:15", "17:45"],
            6: ["18:20", "19:50"],
            7: ["20:00", "21:30"]
        }
    },
}
