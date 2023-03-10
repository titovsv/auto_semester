import os
import platform
import time
import datetime
import config
from csv import writer, DictWriter


class bcolors:
    OK = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    HEADER = '\033[95m'


def print_ext(str, state):
    if state == 'ok':
        print(f"{bcolors.OK}{str}")
    elif state == 'fail':
        print(f"{bcolors.FAIL}{str}")
    elif state == 'warning':
        print(f"{bcolors.WARNING}{str}")
    elif state == 'bold':
        print(f"{bcolors.BOLD}{str}")
    elif state == 'header':
        print(f"{bcolors.HEADER}{str}")
    print(f"{bcolors.ENDC}")


def clear_console():
    opsystem = platform.system()

    if opsystem.lower() == 'windows':
        run_command = 'cls'
    elif opsystem.lower() == 'linux':
        run_command = 'clear'

    def clear(): return os.system(run_command)
    clear()


def get_timestamp(str_date):
    ts = int(time.mktime(datetime.datetime.strptime(
        str_date, config.DATE_FORMAT).timetuple()))
    return ts


def create_file():

    if create_catalog() == False:
        return

    now = datetime.datetime.now()
    date_time = now.strftime("%Y%m%d%H%M%S")
    file_name = config.CATALOG_FOR_RESULT + '/result_' + date_time + '.csv'

    try:
        file = open(file_name, 'w')
        file.close()
    except FileNotFoundError:
        print("Error...")
        file_name = ''

    return file_name


def write_row_to_csv(file_name, dict):

    try:
        with open(file_name, 'w', newline='') as csvfile:
            writer = DictWriter(csvfile, fieldnames=dict[0].keys(), dialect='excel', delimiter=';')
            writer.writeheader()
            for data in dict:
                writer.writerow(data)
    except IOError:
        print("I/O error")

    return True

def create_catalog():

    if config.CATALOG_FOR_RESULT == '':
        catalog = 'tmp'
    else:
        catalog = config.CATALOG_FOR_RESULT

    if os.path.exists(catalog):
        return True

    try:
        os.mkdir(catalog)
        return True
    except OSError as error:
        print(error)
        return False