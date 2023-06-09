import json
import os


def check_dir():
    if not os.path.exists("files"):
        os.mkdir("files")


def check_file(file_name, is_dict=None):
    check_dir()
    if os.path.isfile("files/%s" % file_name):
        return 0
    with open("files/%s" % file_name, "w") as f:
        if is_dict:
            text_to_create_file = "{}"
        else:
            text_to_create_file = ""
        f.write(text_to_create_file)
        return 0


def save_file(file_name, data_to_save, is_dict=None, is_add=None, is_list=None):
    check_file(file_name, is_dict)
    if is_dict:
        with open("files/%s" % file_name, "w") as f:
            f.write(json.dumps(data_to_save, indent=4))
            f.close()
    elif is_add:
        with open("files/%s" % file_name, "a") as f:
            f.write("%s\n" % data_to_save)
            f.close()
    elif is_list:
        with open("files/%s" % file_name, "w") as f:
            [f.write("%s\n" % line) for line in data_to_save]
            f.close()
    else:
        with open("files/%s" % file_name, "w") as f:
            f.write(data_to_save)
            f.close()


def get_file(file_name, is_dict=None, path=True):
    if path:
        path = "files/"
        check_file(file_name, is_dict)
    else:
        path = ""
    with open(f"{path}%s" % file_name, "r", encoding="utf-8") as f:
        if is_dict:
            try:
                data_read = f.read()
                return json.loads(data_read)
            except:
                return {}
        data_read = f.readlines()
        if not data_read:
            print(f"Файл {path}/%s пустой" % file_name)
            return []
        return [line.rstrip() for line in data_read]


def get_settings():
    return get_file("settings.json", is_dict=True)
