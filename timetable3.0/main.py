# !/usr/bin/python
# -*- coding: utf-8 -*-
import copy
import io
import time as _time
from datetime import datetime, timedelta, time
from sys import exc_info
from threading import Thread
from traceback import extract_tb
import json as json_
import requests
from lxml import html
from vk_api.longpoll import VkLongPoll, VkEventType

from scr.vk_functions import *


def thread(my_func):
    def wrapper(*args, **kwargs):
        my_thread = Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()

    return wrapper


emoj_num = ("0⃣", "1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣")
days_of_the_week = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября",
          "декабря"]


def get_replace(url):
    r = requests.get(url, timeout=65)
    r.encoding = 'utf-8'
    site = html.fromstring(r.text)
    elements = site.xpath('//tr')[1:]
    groups = {}
    for element in elements:
        try:
            element = [i.text for i in element.xpath(".//td")[1:]]
            if element[0] is not None:
                element[0] = str(element[0]).upper()
            if not groups.get(element[0]) and element[0] is not None:
                groups.update({element[0].strip(): {}})
            for i in range(len(element)):
                if element[i] is not None:
                    element[i] = element[i].replace("\n", " ")
                    element[i] = element[i].strip()
                if element[i] == " " or element[i] == "":
                    element[i] = None
            if element[0] is None:
                continue
            if element[1] is None:
                groups[element[0]].update({-1: element[2:]})
                continue
            if element[1].isdigit() and len(element[1]) == 1:
                if groups[element[0]].get(int(element[1])):
                    groups[element[0]][int(element[1])] = element[2:]
                else:
                    groups[element[0]].update({int(element[1]): element[2:]})
            elif "-" in element[1]:
                pairs_for = element[1].split("-")
                if len(pairs_for) == 2 and pairs_for[0].isdigit(
                ) and pairs_for[1].isdigit():
                    for i in range(int(pairs_for[0]), int(pairs_for[1]) + 1):
                        groups[element[0]].update({i: element[2:]})
            elif "," in element[1]:
                pairs_for = element[1].split(",")
                for pair in pairs_for:
                    if pair.isdigit():
                        groups[element[0]].update({int(pair): element[2:]})
            elif len(element[1]) != 1 and element[1].isdigit():
                pairs_for = list(element[1])
                for pair in pairs_for:
                    if pair.isdigit():
                        groups[element[0]].update({int(pair): element[2:]})
        except Exception as E:
            print(f"Ошибка {E}\n{str(extract_tb(exc_info()[2]))}")
            msg(f"Ошибка {E}\n{str(extract_tb(exc_info()[2]))}", 194701989)
    day = 0
    dates_replace = site.xpath("//div[@align='center']")
    for date_replace in dates_replace:
        if date_replace.text and "расписании" in date_replace.text:
            day = date_replace.text.split()[3]
    return int(day), groups


def get_date(bias=0):
    now = datetime.now()
    # now = datetime(2021, 1, 9, 12, 40)
    if now.weekday() == 6:
        now += timedelta(days=1)
    elif now.time() > time(12, 00):  # 12, 00 - msk (msk - 3)
        now += timedelta(days=1)
    if now.weekday() == 6:
        now += timedelta(days=1)
    # now += timedelta(days=bias)
    if bias > 0:
        now += timedelta(days=bias)
        if now.weekday() == 6:
            now += timedelta(days=1)
    if bias < 0:
        now += timedelta(days=bias)
        if now.weekday() == 6:
            now += timedelta(days=-1)
    month_out = months[now.month - 1]
    weekday = days_of_the_week[now.weekday()]
    denominator = (now.isocalendar()[1]) % 2
    return {"day": now.day, "month": month_out, "weekday": weekday, "denominator": denominator}


# def resize(file_path):
#     im = Image.open(file_path)
#     img = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
#     i = 0
#     for line in reversed(img):
#         i += 1
#         if [0, 0, 0] in line:
#             break
#     im.crop((0, 115, 800, 4025 - i)).save(file_path)


class TimetableBot:

    def __init__(self):
        # self.groups_timetable = requests.get("https://raw.githubusercontent.com/Bee3yH4uk/"
        #                                      "user-agents/master/groups.txt").json()
        # self.persons_url = "https://jsonblob.com/api/jsonBlob/1bd8983d-6623-11eb-83aa-2995083c2db4"
        with open('groups.txt', 'r', encoding='utf-8') as f:
            self.groups_timetable = json.load(f)
        with open('teacher_timetable.json', 'r', encoding='utf-8') as f:
            self.teacher_timetable = json.load(f)
        self.persons_url = "https://jsonblob.com/api/jsonBlob/882282470825996288"
        self.db = TimetableDatabase()
        self.persons = {}
        self.replacements = {}
        self.teacher_replacements = {}
        self.replacements_photos = ""
        self.clarifying_replace = {}
        self.updating_replacements()
        self.checker_message()
        self.active()

    @thread
    def active(self):
        while True:
            try:
                msg(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3], peer_id=640201107)
            except Exception as E:
                print(E)
            sleep(600)

    def get_users_db(self):
        pass

    def get_users_json(self):
        for i in range(10):
            try:
                response = requests.get(self.persons_url)
                if response.ok:
                    print("Информация о пользователях получена!")
                    self.persons = response.json()
                    break
                sleep(1)
            except Exception as E:
                print(f"Ошибка {E}\n{str(extract_tb(exc_info()[2]))}")
                msg(f"Ошибка {E}\n{str(extract_tb(exc_info()[2]))}", 194701989)

    # def replacements_to_img(self):
    #     try:
    #         urls = [
    #             "https://menu.sttec.yar.ru/timetable/rasp_first.html",
    #             "https://menu.sttec.yar.ru/timetable/rasp_second.html"
    #         ]
    #         hti.screenshot(url=urls[0], save_as='rasp_first.png', size=(800, 4000))
    #         hti.screenshot(url=urls[1], save_as='rasp_second.png', size=(800, 4000))
    #         resize("rasp_first.png")
    #         resize("rasp_second.png")
    #         rasp_first_upload = requests.post(vk.method("photos.getMessagesUploadServer")['upload_url'],
    #                                           files={'photo': open('rasp_first.png', 'rb')}).json()
    #         rasp_second_upload = requests.post(vk.method("photos.getMessagesUploadServer")['upload_url'],
    #                                            files={'photo': open('rasp_second.png', 'rb')}).json()
    #         rasp_first_data = vk.method('photos.saveMessagesPhoto',
    #                                     {'photo': rasp_first_upload['photo'], 'server': rasp_first_upload['server'],
    #                                      'hash': rasp_first_upload['hash']})[0]
    #         rasp_second_data = vk.method('photos.saveMessagesPhoto',
    #                                      {'photo': rasp_second_upload['photo'], 'server': rasp_second_upload['server'],
    #                                       'hash': rasp_second_upload['hash']})[0]
    #         rasp_first = "photo{}_{}".format(rasp_first_data["owner_id"], rasp_first_data["id"])
    #         rasp_second = "photo{}_{}".format(rasp_second_data["owner_id"], rasp_second_data["id"])
    #         self.replacements_photos = f"{rasp_first},{rasp_second}"
    #     except Exception as E:
    #         print(f"Ошибка {E}\n{str(extract_tb(exc_info()[2]))}")
    #         msg(f"Ошибка {E}\n{str(extract_tb(exc_info()[2]))}", 194701989)

    def save_persons(self):
        # try:
        #     headers = {
        #         "Content-Type": "application/json",
        #         "Accept": "application/json",
        #         "x-requested-with": "XMLHttpRequest"
        #     }
        #     requests.put(self.persons_url, headers=headers, data=json.dumps(self.persons))
        # except Exception as E:
        #     print(f"Ошибка {E}\n{str(extract_tb(exc_info()[2]))}")
        #     msg(f"Ошибка {E}\n{str(extract_tb(exc_info()[2]))}", 194701989)
        pass

    def get_all_teacher_replace(self, this_replacements):
        current_teacher_replacements = {}
        for replacement_group_name, replacement in this_replacements.items():
            for pair_number, pair_replacement in replacement.items():
                if not pair_replacement or not pair_replacement[1]:
                    continue
                try:
                    teachers_replace = pair_replacement[1].replace('ё', 'е').replace('.', '') \
                        .replace(',', '').replace('вакансия', '').replace('Вакансия', '').replace('п/гр', '') \
                        .replace("Снято", "").replace("снято", "").replace("-", "").replace(" ", "").strip()
                    if len(teachers_replace) < 5:
                        continue
                    is_good = False
                    for teacher in self.teacher_timetable:
                        current_teacher = teacher.replace('ё', 'е').replace('.', '') \
                            .replace(',', '').replace('вакансия', '').replace('Вакансия', '').replace(" ", "").strip()
                        if current_teacher in teachers_replace:
                            if not teacher in current_teacher_replacements:
                                current_teacher_replacements[teacher] = {}
                            current_teacher_replacements[teacher][pair_number] = [replacement_group_name,
                                                                                  *pair_replacement]
                            is_good = True
                            # break
                    if not is_good:
                        # Вторая проверка
                        for teacher in self.teacher_timetable:
                            if teacher.split(' ')[0] in teachers_replace:
                                if not teacher in current_teacher_replacements:
                                    current_teacher_replacements[teacher] = {}
                                current_teacher_replacements[teacher][pair_number] = [replacement_group_name,
                                                                                      *pair_replacement]
                                is_good = True
                                break
                    if not is_good:
                        print('Не удалось найти учителя:', teachers_replace)
                except Exception as E:
                    print('Получение замен учителей', E)
                    print(f"Ошибка {E}\n{str(extract_tb(exc_info()[2]))}")
        return current_teacher_replacements

    def get_all_replace(self):
        urls = [
            "https://menu.sttec.yar.ru/timetable/rasp_first.html",
            "https://menu.sttec.yar.ru/timetable/rasp_second.html"
        ]
        first = get_replace(urls[0])
        first_teacher = self.get_all_teacher_replace(first[1])
        second = get_replace(urls[1])
        second_teacher = self.get_all_teacher_replace(second[1])
        for key in second_teacher:
            if key not in first_teacher:
                first_teacher[key] = second_teacher[key]
            else:
                first_teacher[key].update(second_teacher[key])
        if first[0] == second[0]:
            return {first[0]: {**first[1], **second[1]}}, {first[0]: first_teacher}
        else:
            self.clarifying_replace = {first[0]: "⚠Замены обновлены только для первой смены",
                                       second[0]: "⚠Замены обновлены только для второй смены"}
            return {first[0]: first[1], second[0]: second[1]}, {first[0]: first_teacher, second[0]: second_teacher}

    @thread
    def updating_replacements(self):
        while True:
            try:
                print("Getting replacements")
                all_replace = self.get_all_replace()
                if isinstance(all_replace, tuple):
                    self.replacements = all_replace[0]
                    self.teacher_replacements = all_replace[1]
                print("Replacements received")
                # self.replacements_to_img()
                sleep(10 * 60)
            except Exception as E:
                print(f"Ошибка {E}\n{str(extract_tb(exc_info()[2]))}")
                sleep(1)

    @thread
    def checker_message(self):
        bot_commands = {
            "Расписание": lambda: self.get_timetable(person_id),
            "Следующее": lambda: self.get_timetable(person_id, bias=1),
            "Предыдущее": lambda: self.get_timetable(person_id, bias=-1),
            "Команды": lambda: msg_keyboard("Выберите кнопку", person_id,
                                            create_commands_keyboard(self.persons.get(person_id))),
            "Назад": lambda: msg_keyboard("Выберите кнопку", person_id, keyboard_main),
            "Нaзад": lambda: msg_keyboard("Выберите кнопку", person_id,
                                          create_commands_keyboard(self.persons.get(person_id))),
            "Замены": lambda: self.out_replacements(person_id),
            "Изменить группу": lambda: self.clear_person(person_id),
            "Рассылка": lambda: None,
            "Расписание звонков": lambda: self.send_call_schedule(person_id),
            "Числитель": lambda: self.get_week_timetable(person_id, denominator=False),
            "Знаменатель": lambda: self.get_week_timetable(person_id, denominator=True),
            "Поддержка": lambda: get_help(person_id)
        }
        sleep(3)
        while True:
            try:
                for message in get_conversations()['items']:
                    last_message = message['last_message']
                    person_id = str(last_message['from_id'])
                    if not message['conversation']['can_write']['allowed']:
                        markAsRead(person_id)
                    elif _time.time() - last_message['date'] > 10:
                        self.persons[person_id] = self.db.get_user(person_id)
                        body = last_message['text']
                        print("[last] %s: %s" % (person_id, body))
                        # if self.persons.get(person_id) is None or (
                        #         self.persons[person_id].get("change_group") is None and self.persons[person_id].get(
                        #     "teacher_name") is None):
                        if self.persons.get(person_id) is None or self.persons[person_id].get('role') is None:
                            self.change_group(person_id, body)
                            continue
                        elif self.persons[person_id]['role'] not in ['Студент', 'Учитель']:
                            self.change_group(person_id, body)
                            continue
                        elif self.persons[person_id].get("change_group") is None and self.persons[person_id].get(
                                'role') == 'Студент':
                            self.change_group(person_id, body)
                            continue
                        elif self.persons[person_id].get("teacher_name") is None and self.persons[person_id].get(
                                'role') == 'Учитель':
                            self.change_group(person_id, body)
                            continue
                        elif body in bot_commands:
                            if person_id in persons_to_get_help:
                                persons_to_get_help.remove(person_id)
                            bot_commands[body]()
                        elif person_id in persons_to_get_help:
                            msg(f"Обращение пользователя @id{person_id}: {body}", 194701989)
                            persons_to_get_help.remove(person_id)
                            msg("Обращение успешно отправлено!", person_id)
                        else:
                            msg_keyboard("Выберите кнопку", person_id, keyboard_main)
                sleep(10)
            except Exception as E:
                print(f"Ошибка {E}\n{str(extract_tb(exc_info()[2]))}")
                # msg(f"Ошибка {E}\n{str(extract_tb(exc_info()[2]))}", 194701989)

    def change_group(self, peer_id, msg_body):
        roles = ['Студент', 'Учитель']
        if self.persons.get(peer_id) is None:
            # departments = self.groups_timetable.keys()
            msg_keyboard("Приветсвуем вас в боте!\nПожалуйста выберите вашу роль", peer_id,
                         create_keyboard(roles, False))
            self.persons[peer_id] = {"sending": 0, "sending_time": "12:00"}
            self.db.add_user(peer_id)
            # self.save_persons()
        elif self.persons[peer_id].get("role") is None or self.persons[peer_id].get("role") not in roles:
            if msg_body in roles:
                self.persons[peer_id]["role"] = msg_body
                self.db.change_user(peer_id, role=msg_body)
                if msg_body == 'Студент':
                    departments = self.groups_timetable.keys()
                    msg_keyboard("Выбрана роль: %s\nВыберите отделение" % msg_body, peer_id,
                                 create_keyboard(departments, True))
                else:
                    teacher_names = self.teacher_timetable.keys()
                    surname = get_surname_by_id(peer_id)
                    teacher_list = [teacher_name for teacher_name in teacher_names if surname in teacher_name]
                    teacher_list = teacher_list if len(teacher_list) < 10 else teacher_list[:9]
                    msg_keyboard("Выберите/введите фамилию преподавателя", peer_id, create_keyboard(teacher_list, True))
            else:
                msg_keyboard("Выберите роль", peer_id, create_keyboard(roles, False))

        elif self.persons[peer_id].get('role') == 'Студент':
            if self.persons[peer_id].get("department") is None:
                departments = self.groups_timetable.keys()
                if msg_body in departments:
                    self.persons[peer_id]["department"] = msg_body
                    self.db.change_user(peer_id, department=msg_body)
                    change_groups = self.groups_timetable[msg_body].keys()
                    msg_keyboard("Выбрано отделение: %s\nВыберите группы" % msg_body, peer_id,
                                 create_keyboard(change_groups, True))
                elif msg_body == "Назад":
                    self.persons[peer_id]["role"] = None
                    self.db.change_user(peer_id, role=None)
                    msg_keyboard("Выберите роль", peer_id, create_keyboard(roles, False))
                else:
                    msg_keyboard("Выберите отделение", peer_id, create_keyboard(departments, True))
                # self.save_persons()
            elif self.persons[peer_id].get("change_groups") is None:
                if self.persons[peer_id]["department"] not in self.groups_timetable:
                    self.clear_person(peer_id)
                    return 0
                change_groups = self.groups_timetable[self.persons[peer_id]["department"]].keys()
                if msg_body in change_groups:
                    self.persons[peer_id]["change_groups"] = msg_body
                    self.db.change_user(peer_id, change_groups=msg_body)
                    change_group = self.groups_timetable[self.persons[peer_id]["department"]][msg_body].keys()
                    msg_keyboard("Выбраны группы: %s\nВыберите группу" % msg_body, peer_id,
                                 create_keyboard(change_group, True))
                elif msg_body == "Назад":
                    departments = self.groups_timetable.keys()
                    self.persons[peer_id]["department"] = None
                    self.db.change_user(peer_id, department=None)
                    msg_keyboard("Выберите отделение", peer_id, create_keyboard(departments, True))
                else:
                    msg_keyboard("Выберите группы", peer_id, create_keyboard(change_groups, False))
                # self.save_persons()
            elif self.persons[peer_id].get("change_group") is None:
                if self.persons[peer_id]["department"] not in self.groups_timetable or \
                        self.persons[peer_id]["change_groups"] not in self.groups_timetable[
                    self.persons[peer_id]["department"]]:
                    self.clear_person(peer_id)
                    return 0
                change_group = self.groups_timetable[self.persons[peer_id]["department"]][
                    self.persons[peer_id]["change_groups"]].keys()
                if msg_body in change_group:
                    self.persons[peer_id]["change_group"] = msg_body
                    self.db.change_user(peer_id, change_group=msg_body)
                    msg_keyboard("Группа успешно выбрана!", peer_id, keyboard_main)
                elif msg_body == "Назад":
                    change_groups = self.groups_timetable[self.persons[peer_id]["department"]].keys()
                    self.persons[peer_id]["change_groups"] = None
                    self.db.change_user(peer_id, change_groups=None)
                    msg_keyboard("Выберите группы", peer_id, create_keyboard(change_groups, True))
                else:
                    msg_keyboard("Выберите группу", peer_id, create_keyboard(change_group, True))
                # self.save_persons()
        else:
            if self.persons[peer_id].get("teacher_name") is None:
                teacher_names = self.teacher_timetable.keys()
                if msg_body in teacher_names:
                    self.persons[peer_id]["teacher_name"] = msg_body
                    self.db.change_user(peer_id, teacher_name=msg_body)
                    msg_keyboard("Преподаватель успешно выбран!", peer_id, keyboard_main)
                elif msg_body == "Назад":
                    self.persons[peer_id]["role"] = None
                    self.db.change_user(peer_id, role=None)
                    msg_keyboard("Выберите роль", peer_id, create_keyboard(roles, False))
                else:
                    teacher_list = [teacher_name for teacher_name in teacher_names if msg_body in teacher_name]
                    teacher_list = teacher_list if len(teacher_list) < 10 else teacher_list[:9]
                    msg_keyboard("Выберите/введите фамилию преподавателя", peer_id, create_keyboard(teacher_list, True))
                # self.save_persons()

    def clear_person(self, person_id_to_clear, send_msg=True):
        # self.persons[person_id_to_clear] = {}
        # self.save_persons()
        roles = ['Студент', 'Учитель']
        self.db.del_user(person_id_to_clear)
        if send_msg:
            msg_keyboard("Выберите роль", person_id_to_clear, create_keyboard(roles, False))

    def check_group_name(self, key, group_name):
        # for this_group_name in group_name.replace(" /", "/").replace("/ ", "/").split("/"):
        try:
            if group_name.replace(" /", "/").replace("/ ", "/").split("/")[0] in key:
                print(key, group_name.replace(" /", "/").replace("/ ", "/").split("/")[0])
                return 1
        except Exception as E:
            print(f"Ошибка {E}\n{str(extract_tb(exc_info()[2]))}")
            msg(f"Ошибка {E}\n{str(extract_tb(exc_info()[2]))}", 194701989)
        return key in group_name

    def get_replacements_teacher(self, day, teacher_name):
        try:
            this_replacements_day = self.teacher_replacements.get(day)
            this_replacements_group = {}
            if this_replacements_day:
                for key in this_replacements_day.keys():
                    if key is not None and teacher_name == key:
                        this_replacements_group.update(copy.deepcopy(this_replacements_day.get(key)))
                if len(self.replacements.keys()) == 1:
                    replacements_info = "✅C проверкой замен"
                else:
                    replacements_info = self.clarifying_replace.get(day)
                    if not replacements_info:
                        replacements_info = "⚠Замены обновлены частично"
            else:
                replacements_info = "❗Замены на сайте не обновлены"
            return this_replacements_group, replacements_info
        except Exception as E:
            print("Ошибка get_replacements:" + str(E), extract_tb(exc_info()[2]))
            msg("Ошибка get_replacements:\n" + str(E) + '\n' + str(extract_tb(exc_info()[2])), 194701989)
            return {}, "⚠Ошибка получения замен"

    def get_replacements(self, day, group_name):
        try:
            this_replacements_day = self.replacements.get(day)
            this_replacements_group = {}
            if this_replacements_day:
                for key in this_replacements_day.keys():
                    if not key or not group_name:
                        continue
                    if key is not None and self.check_group_name(key.replace("C", "С"), group_name.replace("C", "С")):
                        this_replacements_group.update(copy.deepcopy(this_replacements_day.get(key)))
                if len(self.replacements.keys()) == 1:
                    replacements_info = "✅C проверкой замен"
                else:
                    replacements_info = self.clarifying_replace.get(day)
                    if not replacements_info:
                        replacements_info = "⚠Замены обновлены частично"
            else:
                replacements_info = "❗Замены на сайте не обновлены"
            return this_replacements_group, replacements_info
        except Exception as E:
            print("Ошибка get_replacements:" + str(E), extract_tb(exc_info()[2]))
            msg("Ошибка get_replacements:\n" + str(E) + '\n' + str(extract_tb(exc_info()[2])), 194701989)
            return {}, "⚠Ошибка получения замен"

    def get_teacher_replacements(self, day):
        try:
            this_replacements_day = self.replacements.get(day)
            current_teacher_replacements = {}
            if this_replacements_day:

                if len(self.replacements.keys()) == 1:
                    replacements_info = "✅C проверкой замен"
                else:
                    replacements_info = self.clarifying_replace.get(day)
                    if not replacements_info:
                        replacements_info = "⚠Замены обновлены частично"
            else:
                replacements_info = "❗Замены на сайте не обновлены"
            return current_teacher_replacements, replacements_info
        except Exception as E:
            print("Ошибка get_teacher_replacements:" + str(E), extract_tb(exc_info()[2]))
            msg("Ошибка get_teacher_replacements:\n" + str(E) + '\n' + str(extract_tb(exc_info()[2])), 194701989)
            return {}, "⚠Ошибка получения замен"

    def get_group_by_id(self, this_person_id):
        this_person = self.persons.get(this_person_id)
        # this_person = self.db.get_user(this_person_id)
        if not this_person:
            return 0
        if not this_person.get('department') or not this_person.get('change_groups') or not this_person.get(
                'change_group'):
            return 0
        this_department = self.groups_timetable.get(this_person.get('department'))
        if not this_department:
            self.clear_person(this_person_id)
            return 0
        this_groups = this_department.get(this_person.get('change_groups'))
        if not this_groups:
            self.clear_person(this_person_id)
            return 0
        this_group = this_groups.get(this_person.get('change_group'))
        if not this_group:
            self.clear_person(this_person_id)
            return 0
        return this_department, this_groups, this_group

    def get_timetable_teacher(self, this_person_id, bias=0):
        this_date = get_date(bias)
        this_timetable = copy.deepcopy(
            self.teacher_timetable[self.persons[this_person_id]['teacher_name']].get(this_date['weekday']))
        if not this_timetable:
            this_timetable = {}
        for pair in this_timetable:
            if this_date['denominator']:
                this_timetable[pair] = this_timetable[pair].pop('denominator', None)
            else:
                this_timetable[pair] = this_timetable[pair].pop('numerator', None)
        this_replacements_group, replacements_info = self.get_replacements_teacher(this_date['day'],
                                                                                   self.persons[this_person_id][
                                                                                       'teacher_name'])
        print(this_replacements_group, replacements_info)
        if this_replacements_group:
            for this_replacement in this_replacements_group:
                if this_replacement == -1:
                    continue
                this_timetable[str(this_replacement)] = {"subject": this_replacements_group[this_replacement][1],
                                                         "audience": this_replacements_group[this_replacement][3],
                                                         "group": this_replacements_group[this_replacement][0],
                                                         "teacher": "❗замена"}
        timetable_keys = list(this_timetable.keys())
        timetable_keys.sort()
        timetable_str = f"Расписание на {this_date['day']} {this_date['month']}, {this_date['weekday'].lower()} "
        if this_date['denominator']:
            timetable_str += "(знаменатель):\n"
        else:
            timetable_str += "(числитель):\n"
        for pair in timetable_keys:
            if not pair:
                continue
            this_pair = this_timetable.get(pair)
            if not this_pair:
                continue
            if pair.isdigit() and 0 <= int(pair) <= 8:
                timetable_str += f"{emoj_num[int(pair)]} "
            else:
                timetable_str += f"{pair} "
            if this_pair.get('audience'):
                timetable_str += f"[{str(this_pair['audience']).replace('  ', ' ')}] "
            if self.persons[this_person_id].get('show_start_pair'):
                this_department_to_time = 'ОИТУП'
                if pair.isdigit() and 0 <= int(pair) < 8 and CALL_SCHEDULE[this_department_to_time][
                    'saturday' if this_date['weekday'] == 'Суббота' else 'workweek'].get(int(pair)):
                    timetable_str += f"({CALL_SCHEDULE[this_department_to_time]['saturday' if this_date['weekday'] == 'Суббота' else 'workweek'][int(pair)][0]}) "
            # if this_pair.get('subject'):
            #     timetable_str += f"{this_pair['subject']} "
            if this_pair.get('subject'):
                timetable_str += f"{this_pair['subject']} "
            if this_pair.get('group'):
                if isinstance(this_pair['group'], list):
                    timetable_str += f"({this_pair['group'][-1].split('/')[0]}) "
                else:
                    timetable_str += f"({this_pair['group']}) "
            if this_pair.get('teacher'):
                timetable_str += f" {this_pair['teacher']}"
            timetable_str += "\n"
        if this_replacements_group and -1 in this_replacements_group:
            timetable_str += f"❗ [{this_replacements_group[-1][-1]}] {this_replacements_group[-1][1]}"
        if not timetable_keys:
            timetable_str += "✅Нет пар"
        timetable_str += "\n" + replacements_info
        msg_keyboard(timetable_str, this_person_id, keyboard_main)

    @thread
    def get_timetable(self, this_person_id, bias=0):
        this_person = self.persons.get(this_person_id)
        # this_person = self.db.get_user(this_person_id)
        if this_person['role'] == 'Учитель':
            self.get_timetable_teacher(this_person_id, bias)
            return 0
        this_person_group = self.get_group_by_id(this_person_id)
        if not this_person_group:
            return 0
        this_department, this_groups, this_group = this_person_group
        this_date = get_date(bias)
        # {'day': 6, 'month': 'февраля', 'weekday': 'Суббота', 'denominator': 1}
        this_timetable = copy.deepcopy(this_group.get(this_date['weekday']))
        for pair in this_timetable:
            if this_date['denominator']:
                this_timetable[pair] = this_timetable[pair].pop('denominator', None)
            else:
                this_timetable[pair] = this_timetable[pair].pop('numerator', None)
        this_replacements_group, replacements_info = self.get_replacements(this_date['day'],
                                                                           this_person.get('change_group'))
        if this_replacements_group:
            for this_replacement in this_replacements_group:
                if this_replacement == -1:
                    continue
                this_timetable[str(this_replacement)] = {"subject": this_replacements_group[this_replacement][1],
                                                         "audience": this_replacements_group[this_replacement][2],
                                                         "teacher": "❗замена"}
        timetable_keys = list(this_timetable.keys())
        timetable_keys.sort()
        if '8.00' in timetable_keys:
            timetable_keys.insert(0, timetable_keys.pop())
        timetable_str = f"Расписание на {this_date['day']} {this_date['month']}, {this_date['weekday'].lower()} "
        if this_date['denominator']:
            timetable_str += "(знаменатель):\n"
        else:
            timetable_str += "(числитель):\n"
        for pair in timetable_keys:
            if not pair:
                continue
            this_pair = this_timetable.get(pair)
            if not this_pair:
                continue
            if pair.isdigit() and 0 <= int(pair) <= 8:
                timetable_str += f"{emoj_num[int(pair)]} "
            else:
                timetable_str += f"{pair} "
            if this_pair.get('audience'):
                timetable_str += f"[{str(this_pair['audience']).replace('  ', ' ')}] "
            if self.persons[this_person_id].get('show_start_pair'):
                this_department_to_time = this_person['department']
                if this_department_to_time == 'ММО':
                    this_department_to_time = 'ММО'
                elif 'ОЭП' in this_department_to_time:
                    this_department_to_time = 'ОЭП'
                else:
                    this_department_to_time = 'ОИТУП'
                if pair.isdigit() and 0 <= int(pair) < 8 and CALL_SCHEDULE[this_department_to_time][
                    'saturday' if this_date['weekday'] == 'Суббота' else 'workweek'].get(int(pair)):
                    timetable_str += f"({CALL_SCHEDULE[this_department_to_time]['saturday' if this_date['weekday'] == 'Суббота' else 'workweek'][int(pair)][0]}) "
            if this_pair.get('subject'):
                timetable_str += f"{this_pair['subject']} "
            if this_pair.get('teacher'):
                timetable_str += f"({this_pair['teacher']})"
            timetable_str += "\n"
        if this_replacements_group and -1 in this_replacements_group:
            timetable_str += f"❗ [{this_replacements_group[-1][-1]}] {this_replacements_group[-1][1]}"
        if not timetable_keys:
            timetable_str += "✅Нет пар"
        timetable_str += "\n" + replacements_info
        msg_keyboard(timetable_str, this_person_id, keyboard_main)

    def out_replacements_teacher(self, this_person_id):
        this_person = self.persons.get(this_person_id)
        this_date = get_date()
        this_replacements_group, replacements_info = self.get_replacements_teacher(this_date['day'],
                                                                                   this_person.get('teacher_name'))
        out_replacements_text = "Замены на %s %s, %s:\n" % (
            this_date["day"], this_date["month"], this_date["weekday"].lower())
        if replacements_info == "❗Замены на сайте не обновлены":
            out_replacements_text += replacements_info
        else:
            if not this_replacements_group:
                out_replacements_text += "✅Замен нет"
            else:
                for pair_key in this_replacements_group:
                    if pair_key == -1:
                        continue
                    this_pair = this_replacements_group[pair_key]
                    out_replacements_text += f"❗{pair_key} пара "
                    if this_pair[1]:
                        out_replacements_text += f"{this_pair[1]} "
                    if this_pair[0]:
                        out_replacements_text += f"({this_pair[0]}), "
                    if this_pair[2]:
                        out_replacements_text += f"заменена на {this_pair[2]}"
                    if this_pair[3]:
                        out_replacements_text += f", кабинет {this_pair[3]}"
                    out_replacements_text += "\n"
        if this_replacements_group and -1 in this_replacements_group:
            out_replacements_text += f"❗ [{this_replacements_group[-1][-1]}] {this_replacements_group[-1][1]}"
        if replacements_info not in ["❗Замены на сайте не обновлены", "✅C проверкой замен"]:
            out_replacements_text += "\n" + replacements_info
        msg_keyboard(out_replacements_text, this_person_id, keyboard_main)

    def out_replacements(self, this_person_id):
        this_person = self.persons.get(this_person_id)
        # this_person = self.db.get_user(this_person_id)
        if this_person['role'] == 'Учитель':
            self.out_replacements_teacher(this_person_id)
            return 0
        this_date = get_date()
        this_replacements_group, replacements_info = self.get_replacements(this_date['day'],
                                                                           this_person.get('change_group'))
        out_replacements_text = "Замены на %s %s, %s:\n" % (
            this_date["day"], this_date["month"], this_date["weekday"].lower())
        if replacements_info == "❗Замены на сайте не обновлены":
            out_replacements_text += replacements_info
        else:
            if not this_replacements_group:
                out_replacements_text += "✅Замен нет"
            else:
                for pair_key in this_replacements_group:
                    if pair_key == -1:
                        continue
                    this_pair = this_replacements_group[pair_key]
                    out_replacements_text += f"❗{pair_key} пара "
                    if this_pair[0]:
                        out_replacements_text += f"{this_pair[0]} "
                    out_replacements_text += f"заменена на {this_pair[1]}"
                    if this_pair[2]:
                        out_replacements_text += f", кабинет {this_pair[2]}"
                    out_replacements_text += "\n"
        if this_replacements_group and -1 in this_replacements_group:
            out_replacements_text += f"❗ [{this_replacements_group[-1][-1]}] {this_replacements_group[-1][1]}"
        if replacements_info not in ["❗Замены на сайте не обновлены", "✅C проверкой замен"]:
            out_replacements_text += "\n" + replacements_info
        msg_keyboard(out_replacements_text, this_person_id, keyboard_main)

    def get_week_timetable_teacher(self, this_person_id, denominator):
        this_teacher_name = self.persons.get(this_person_id)['teacher_name']
        this_teacher_timetable = self.teacher_timetable[this_teacher_name]
        out_week_timetable = "Расписание на неделю "
        if denominator:
            out_week_timetable += "(знаменатель)\n"
        else:
            out_week_timetable += "(числитель)\n"
        for week_day in this_teacher_timetable:
            out_week_timetable += week_day + "\n"
            for pair_num in this_teacher_timetable[week_day]:
                if denominator:
                    pair = this_teacher_timetable[week_day][pair_num].get('denominator')
                else:
                    pair = this_teacher_timetable[week_day][pair_num].get('numerator')
                if pair:
                    if pair_num.isdigit() and 0 <= int(pair_num) <= 8:
                        out_week_timetable += emoj_num[int(pair_num)]
                    else:
                        out_week_timetable += f"{pair_num} "
                    out_week_timetable += f"[{pair.get('audience')}] {pair.get('subject')} ({pair.get('group')[2].split('/')[0]})\n"
            out_week_timetable += "\n"
        msg_keyboard(out_week_timetable, this_person_id, create_commands_keyboard(self.persons.get(this_person_id)))

    def get_week_timetable(self, this_person_id, denominator):
        if self.persons.get(this_person_id)['role'] == 'Учитель':
            self.get_week_timetable_teacher(this_person_id, denominator)
            return 0
        person_info = self.get_group_by_id(this_person_id)
        if not person_info:
            return 0
        this_group = person_info[-1]
        out_week_timetable = "Расписание на неделю "
        if denominator:
            out_week_timetable += "(знаменатель)\n"
        else:
            out_week_timetable += "(числитель)\n"
        for week_day in this_group:
            out_week_timetable += week_day + "\n"
            for pair_num in this_group[week_day]:
                if denominator:
                    pair = this_group[week_day][pair_num].get('denominator')
                else:
                    pair = this_group[week_day][pair_num].get('numerator')
                if pair:
                    if pair_num.isdigit() and 0 <= int(pair_num) <= 8:
                        out_week_timetable += emoj_num[int(pair_num)]
                    else:
                        out_week_timetable += f"{pair_num} "
                    out_week_timetable += f"[{pair.get('audience')}] {pair.get('subject')} ({pair.get('teacher')})\n"
            out_week_timetable += "\n"
        msg_keyboard(out_week_timetable, this_person_id, create_commands_keyboard(self.persons.get(this_person_id)))

    def get_person_time(self, this_person_id):
        this_person = self.persons.get(this_person_id)
        # this_person = self.db.get_user(this_person_id)
        this_person_group = self.get_group_by_id(this_person_id)
        if not this_person_group:
            return 0
        this_department, this_groups, this_group = this_person_group
        this_date = get_date()
        # {'day': 6, 'month': 'февраля', 'weekday': 'Суббота', 'denominator': 1}
        this_timetable = copy.deepcopy(this_group.get(this_date['weekday']))
        for pair in this_timetable:
            if this_date['denominator']:
                this_timetable[pair] = this_timetable[pair].pop('denominator', None)
            else:
                this_timetable[pair] = this_timetable[pair].pop('numerator', None)
        this_replacements_group, replacements_info = self.get_replacements(this_date['day'],
                                                                           this_person.get('change_group'))
        if this_replacements_group:
            for this_replacement in this_replacements_group:
                if this_replacement == -1:
                    continue
                this_timetable[str(this_replacement)] = {"subject": this_replacements_group[this_replacement][1],
                                                         "audience": this_replacements_group[this_replacement][2],
                                                         "teacher": "❗замена"}
        timetable_keys = list(this_timetable.keys())
        timetable_keys.sort()
        for pair in timetable_keys:
            if not pair:
                continue
            this_pair = this_timetable.get(pair)
            if this_pair and 'снято' not in str(this_pair['subject']).lower():
                return pair

    def send_call_schedule(self, person_id):
        this_person_departament = self.persons.get(person_id).get('department')
        if self.persons.get(person_id)['role'] == 'Учитель':
            msg("Расписание звонков", person_id, attachment="photo-192403571_457239256")
        # this_person_departament = self.db.get_user(person_id).get('department')
        if not this_person_departament:
            return 0
        if this_person_departament == 'ММО':
            msg("Расписание звонков", person_id, attachment="photo-192403571_457239258")
        elif 'ОЭП' in this_person_departament:
            msg("Расписание звонков", person_id, attachment="photo-192403571_457239257")
        else:
            msg("Расписание звонков", person_id, attachment="photo-192403571_457239259")

    def switch_show_time(self, person_id):
        this_persons = self.persons.get(person_id)
        if not this_persons:
            return 0

        if not this_persons.get('show_start_pair'):
            this_persons['show_start_pair'] = False

        if this_persons['show_start_pair']:
            this_persons['show_start_pair'] = False
            text_to_send = "Отображение началы пары отключено"
            self.db.change_user(person_id, show_start_pair=False)
        else:
            this_persons['show_start_pair'] = True
            text_to_send = "Отображение началы пары включено"
            self.db.change_user(person_id, show_start_pair=True)

        msg_keyboard(text_to_send, person_id, create_commands_keyboard(this_persons))


persons_to_get_help = []


# MainBot = TimeTableBot()
# sleep(.2)
# with open("save_persons", 'r', encoding='utf-8') as f:
#     all_persons = json.load(f)
# for k, person in enumerate(all_persons):
#     print(f"[{k}]", MainBot.get_person_time(person))
# input()

def get_help(person_id):
    msg("Напишите ваше обращение", person_id)
    persons_to_get_help.append((person_id))


def send_abstract(event, user_id):
    pass

# @thread
# def send_abstract(event, user_id):
#     is_good = False
#     document = Document()
#     p = document.add_paragraph()
#     r = p.add_run()
#     sections = document.sections
#     for section in sections:
#         section.top_margin = Pt(10)
#         section.bottom_margin = Pt(10)
#         section.left_margin = Pt(30)
#         section.right_margin = Pt(30)
#     for item in event['items'][0]['attachments']:
#         if item['type'] != 'photo':
#             continue
#         is_good = True
#         photo_sizes = {size['height']: size['url'] for size in item['photo']['sizes']}
#         url = photo_sizes[max(photo_sizes.keys())]
#         img = requests.get(url).content
#         file = io.BytesIO(img)
#         width = 555
#         img = Image.open(file)
#         ratio = (width / float(img.size[0]))
#         height = int((float(img.size[1]) * float(ratio)))
#         r.add_picture(file, width=Pt(width), height=Pt(height))
#     if not is_good:
#         return 0
#     msg('⌚Документ создаётся..', user_id)
#     file = io.BytesIO()
#     file_name = get_surname_by_id(user_id) + ".docx"
#     file.name = file_name
#     document.save(file)
#     file.seek(0)
#     upload_url = vk_.docs.getMessagesUploadServer(type='doc', peer_id=user_id)['upload_url']
#     response = requests.post(upload_url, files={'file': file})
#     result = json_.loads(response.text)
#     file = result['file']
#     file_info = vk_.docs.save(file=file, title=file_name, tags=[])
#     owner_id = file_info['doc']['owner_id']
#     photo_id = file_info['doc']['id']
#     vk.method("messages.send", {'peer_id': user_id, 'random_id': random.randint(1, 2147483647), 'attachment': f"doc{owner_id}_{photo_id}"})


def main():
    MainBot = TimetableBot()
    bot_commands = {
        "Расписание": lambda: MainBot.get_timetable(person_id),
        "Следующее": lambda: MainBot.get_timetable(person_id, bias=1),
        "Предыдущее": lambda: MainBot.get_timetable(person_id, bias=-1),
        "Команды": lambda: msg_keyboard("Выберите кнопку", person_id,
                                        create_commands_keyboard(MainBot.persons.get(person_id))),
        "Назад": lambda: msg_keyboard("Выберите кнопку", person_id, keyboard_main),
        "Нaзад": lambda: msg_keyboard("Выберите кнопку", person_id,
                                      create_commands_keyboard(MainBot.persons.get(person_id))),
        "Отображать начало пары": lambda: MainBot.switch_show_time(person_id),
        "Замены": lambda: MainBot.out_replacements(person_id),
        "Изменить группу": lambda: MainBot.clear_person(person_id),
        "Рассылка": lambda: None,
        "Расписание звонков": lambda: MainBot.send_call_schedule(person_id),
        "Числитель": lambda: MainBot.get_week_timetable(person_id, denominator=False),
        "Знаменатель": lambda: MainBot.get_week_timetable(person_id, denominator=True),
        "Поддержка": lambda: get_help(person_id),
        # "Замены на сайте": lambda: msg("Замены на сайте", person_id, attachment=MainBot.replacements_photos)
    }

    longpoll = VkLongPoll(vk)
    for event in longpoll.listen():
        try:
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    try:
                        msg_ = vk_.messages.getById(message_ids=event.message_id)
                        if event.attachments['attach1_type'] == 'photo':
                            send_abstract(msg_, event.user_id)
                            continue
                    except:
                        pass
                    person_id = event.user_id
                    person_id = str(person_id)
                    body = event.text
                    this_person_db = MainBot.db.get_user(person_id)
                    MainBot.persons[person_id] = this_person_db
                    print("%s: %s" % (person_id, body))
                    # if self.persons.get(person_id) is None or (self.persons[person_id].get("change_group") is None and self.persons.get("teacher_name") is None):
                    # if MainBot.persons.get(person_id) is None or (
                    #         MainBot.persons[person_id].get("change_group") is None and MainBot.persons[person_id].get(
                    #     "teacher_name") is None):
                    #     MainBot.change_group(person_id, body)
                    if MainBot.persons.get(person_id) is None or MainBot.persons[person_id].get('role') is None:
                        MainBot.change_group(person_id, body)
                        continue
                    elif MainBot.persons[person_id]['role'] not in ['Студент', 'Учитель']:
                        MainBot.change_group(person_id, body)
                        continue
                    elif MainBot.persons[person_id].get("change_group") is None and MainBot.persons[person_id].get(
                            'role') == 'Студент':
                        MainBot.change_group(person_id, body)
                        continue
                    elif MainBot.persons[person_id].get("teacher_name") is None and MainBot.persons[person_id].get(
                            'role') == 'Учитель':
                        MainBot.change_group(person_id, body)
                        continue
                    elif body in bot_commands:
                        if person_id in persons_to_get_help:
                            persons_to_get_help.remove(person_id)
                        bot_commands[body]()
                    elif person_id in persons_to_get_help:
                        msg(f"Обращение пользователя @id{person_id}: {body}", 194701989)
                        persons_to_get_help.remove(person_id)
                        msg("Обращение успешно отправлено!", person_id)
                    else:
                        msg_keyboard("Выберите кнопку", person_id, keyboard_main)
        except Exception as Err_execute:
            print(Err_execute)
            try:
                msg("Перезапуск, ошибка:\n" + str(Err_execute) + str(extract_tb(exc_info()[2])), 194701989)
                pass
            except:
                pass
            del MainBot.db
            del longpoll, MainBot
            return 0


while True:
    try:
        main()
    except Exception as Err_execute:
        print(Err_execute)
        try:
            msg("Перезапуск, 0шибка:\n" + str(Err_execute) + str(extract_tb(exc_info()[2])), 194701989)
            pass
        except:
            pass
