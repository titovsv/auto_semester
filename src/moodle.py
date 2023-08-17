
from tabulate import tabulate
import csv
import defs
import http_request
import config
import mssql


result_list = list()


def create_categories(name='', idnumber='', parent=''):

    try:
        new_categories = http_request.call('core_course_create_categories',
                                           categories=[{'name': name,
                                                        'parent': parent,
                                                        'idnumber': idnumber}])
        return new_categories
    except Exception as err:
        if hasattr(err, 'message'):
            print(err.message)
        else:
            print(err)


def create_semester():

    defs.clear_console()

    bcolors = defs.bcolors
    print_ext = defs.print_ext

    path_to_file = input(
        f"{bcolors.WARNING}Input path to csv file with data: {bcolors.ENDC}")
    defs.clear_console()
    try:
        csv_file = open(path_to_file, newline='', encoding='utf-8-sig')
    except FileNotFoundError:
        print(f"File {path_to_file} not found!")
        return
    except PermissionError:
        print(f"Insufficient permission to read {path_to_file}!")
        return
    except IsADirectoryError:
        print(f"{path_to_file} is a directory!")
        return
    csv_data = list(csv.DictReader(csv_file, delimiter=","))

    list_from_csv = list()  # From this list will display user csv file content

    for row in csv_data:
        list_from_csv.append([i for i in row.values()])

    print('Data from csv file:\n')
    print(f"{bcolors.HEADER}")
    print(tabulate(list_from_csv,
                   headers=csv_data[0].keys(),
                   tablefmt='orgtbl'))
    print(f"{bcolors.ENDC}", "\n")

    user_input = input(
        "Check printed data', Is it Ok? 'Y' to continue, 'N' to abort: ")

    if (user_input.lower() not in ["y", "n"]):
        print(f"{bcolors.FAIL}Unknown input, please start again{bcolors.ENDC}")
        return

    if (user_input.lower() == "n"):
        print('User aborted')
        return
    defs.clear_console()
    print_ext('Start work with moodle site...', 'warning')

    i = 1

    for row in csv_data:

        if (row['cat_name'] == '' and
                row['course_template'] == ''):

            append_list_result(csv_row=i,
                               errors='Rows cat_name and course_template is reqired')
            i += 1
            continue

        course_need_to_update = False
        use_previous_category = False

        if (row['cat_name'] != ''):
            category_name = row['cat_name']
        elif (row['cat_name'] == '' and category_name):  # category_name filled previously that`s why we can use it
            use_previous_category = True
        else:
            print_ext('Category name is reqired', 'fail')
            append_list_result(csv_row=i, errors='Category name is reqired')
            i += 1
            continue

        if (row['cat_idnumber'] != ''):
            category_idnumber = row['cat_idnumber']
        # category_idnumber filled previously that`s why we can use it:
        elif (row['cat_name'] == '' and use_previous_category is False):
            print_ext('Category idnumber is reqired', 'fail')
            append_list_result(csv_row=i, errors='Category idnumber is reqired')
            i += 1
            continue

        if (row['parent_idnumber'] != ''):
            parent = row['parent_idnumber']
        elif (row['parent_idnumber'] == '' and use_previous_category is False):
            print_ext('Category parent_idnumber is reqired', 'fail')
            append_list_result(csv_row=i,
                               errors='Category parent_idnumber is reqired')
            i += 1
            continue

        # for result file
        new_cat = ''
        new_course = ''

        if (parent == 0 or parent == "0"):
            category_parent = 0
        else:
            category_parent = get_category_id(criteria_value=parent)

        if (category_parent < 0):
            append_list_result(csv_row=i,
                               errors="No parent category with idnumber "
                               + row['parent_idnumber'])
            i += 1
            continue

        result = get_category_id(criteria_value=category_idnumber)

        if (isinstance(result, int) and result < 0):
            result = create_categories(category_name,
                                       category_idnumber,
                                       category_parent)

            if (isinstance(result, list)):
                print_ext("Created category with id "
                          + str(result[0]['id']),
                          'ok')
                new_cat = config.URL + \
                    config.CATEGORY_VIEW_ENDPOINT + str(result[0]['id'])
            else:
                print_ext("Error creating category with id "
                          + str(result[0]['id']),
                          'fail')
                append_list_result(csv_row=i,
                                   errors="Error creating category "
                                   + str(category_name))

                i += 1
                continue
        else:
            result = [{'id': result}]

        course_template = row['course_template']

        if (row['feedback'] != ''):
            course_template = row['course_template'] + '_' + row['feedback']

        if (course_template != ''):

            cid = get_course_id(course_template)

            if (cid > 0):

                print_ext("Copy course " +
                          str(course_template) +
                          " to category " + str(category_name),
                          'warning')
            else:
                append_list_result(csv_row=i,
                                   category_link=new_cat,
                                   errors="Course template not found "
                                   + str(course_template))

                print_ext("Course template not found " +
                          str(course_template) + ". Check csv row: " + str(i),
                          'fail')
                i += 1
                continue

            course_category = result[0]['id']
            course_name = row['course_name']
            course_shortname = row['course_shortname']

            duplicate_result = dublicate_course(course_category,
                                                cid,
                                                course_name,
                                                course_shortname)

            if (isinstance(duplicate_result, dict) and 'errorcode' in duplicate_result):
                print(duplicate_result['message'])
                append_list_result(csv_row=i,
                                   category_link=new_cat,
                                   errors=str(duplicate_result['message']))
                i += 1
                continue

            if (isinstance(duplicate_result, dict) and 'id' in duplicate_result):
                print_ext("Course duplicated. Id " +
                          str(duplicate_result['id']), 'ok')

                # get course modules for next modifiction
                modules = get_course_content(duplicate_result['id'])

                new_course = config.URL + config.COURSE_VIEW_ENDPOINT + \
                    str(duplicate_result['id'])

                settings_link = config.URL + config.COURSE_SETTINGS_ENDPOINT + \
                    str(duplicate_result['id'])
                users_link = config.URL + config.COURSE_USERS_ENDPOINT + \
                    str(duplicate_result['id'])
                grades_link = config.URL + config.COURSE_GRADES_ENDPOINT + \
                    str(duplicate_result['id'])
                report_link = config.URL + config.COURSE_REPORTS_ENDPOINT + \
                    str(duplicate_result['id'])

                attendance_link = ''

                for mod in modules:
                    if (mod['name'] == 'Attendance'):

                        attendance_link = config.URL + \
                            config.COURSE_MOD_ATTENDANCE_ENDPOINT + \
                            str(mod['id'])

                course_need_to_update = row['course_idnumber'] != ''
            else:
                print_ext("Error duplicate course " +
                          str(course_template) + " For detailes look above",
                          'fail')
                append_list_result(csv_row=i, category_link=new_cat,
                                   errors='Error duplicate course')
                i += 1
                continue

            if (course_need_to_update):

                start = defs.get_timestamp(row['course_start'])
                end = defs.get_timestamp(row['course_end'])
                feedback_start = defs.get_timestamp(row['feedback_start'])
                feedback_end = defs.get_timestamp(row['feedback_end'])
                telegram_chat = row['telegram_chat']
                telegram_channel = row['telegram_channel']
                syllabus = row['syllabus']
                summary = "<div> \
                                <div> \
                                    Telegram_chat:&nbsp;<a href=\"" + telegram_chat + "\">" + telegram_chat + "</a><br> \
                                </div> \
                                <div> \
                                    Telegram_channel:&nbsp;<a href=\"" + telegram_channel + "\">" + telegram_channel + "</a><br> \
                                </div> \
                                <div> \
                                    EduWiki:&nbsp;<a href=\"" + syllabus + "\">" + syllabus + "</a> \
                                </div> \
                            </div>"

                if (row['course_visible'] in 'Yes|yes|1|True|true'):
                    course_visible = '1'
                else:
                    course_visible = '0'

                print('Update course ' + row['course_idnumber'])

                update_result = update_course(id=duplicate_result['id'],
                                              idnumber=row['course_idnumber'],
                                              startdate=start,
                                              enddate=end,
                                              visible=course_visible,
                                              summary=summary)

                if (update_result['warnings']):

                    print(update_result['warnings'])

                    append_list_result(csv_row=i,
                                       category_link=new_cat,
                                       course_link=new_course,
                                       settings_link=settings_link,
                                       users_link=users_link,
                                       grades_link=grades_link,
                                       report_link=report_link,
                                       attendance_link=attendance_link,
                                       errors='Course update warnings: ' +
                                              str(update_result['warnings']))
                else:
                    append_list_result(csv_row=i,
                                       category_link=new_cat,
                                       course_link=new_course,
                                       settings_link=settings_link,
                                       users_link=users_link,
                                       grades_link=grades_link,
                                       report_link=report_link,
                                       attendance_link=attendance_link)

                # Update course modules in mssql

                modules_info = []

                for module in modules:

                    if (module['name'] == 'Telegram chat'
                            and module['modname'] == 'url'):
                        modules_info.append({'table': 'mdl_url',
                                             'id': module['instance'],
                                             'value': telegram_chat,
                                             'modname': module['modname']})

                    elif (module['name'] == 'Telegram channel'
                            and module['modname'] == 'url'):
                        modules_info.append({'table': 'mdl_url',
                                             'id': module['instance'],
                                             'value': telegram_channel,
                                             'modname': module['modname']})

                    elif (module['name'] == 'Feedback'
                          and module['modname'] == 'feedback'):
                        modules_info.append({'table': 'mdl_feedback',
                                             'id': module['instance'],
                                             'value': {'start': feedback_start,
                                                       'end': feedback_end},
                                             'modname': module['modname']})
                    elif (module['name'] == 'Syllabus'
                          and module['modname'] == 'url'):
                        modules_info.append({'table': 'mdl_url',
                                             'id': module['instance'],
                                             'value': syllabus,
                                             'modname': module['modname']})

                if (modules_info):
                    result = update_course_modules_mssql(modules_info)
                    if (result is False):
                        print_ext('Error sql query commit', 'fail')

            else:
                append_list_result(csv_row=i,
                                   category_link=new_cat,
                                   course_link=new_course,
                                   settings_link=settings_link,
                                   users_link=users_link,
                                   grades_link=grades_link,
                                   report_link=report_link,
                                   attendance_link=attendance_link)
        else:
            append_list_result(csv_row=i, category_link=new_cat)
        i += 1

    write_result(result_list)
    print('Done')


def get_course_content(courseid):
    modules = []

    content = http_request.call('core_course_get_contents',
                                courseid=courseid)
    if (type(content) != list):
        print("Error get_course_content " + content.get('exception'))
        return modules
    for module in content[0]['modules']:
        modules.append({'id': module['id'],
                        'instance': module['instance'],
                        'name': module['name'],
                        'modname': module['modname']})

    return modules


def update_course_modules_mssql(modules_info):

    query_url_template = """UPDATE mdl_url SET externalurl = ?
                                WHERE id = ?;"""

    query_feedback_template = """UPDATE mdl_feedback SET timeopen = ?,
                                    timeclose = ? WHERE id = ?"""

    for element in modules_info:

        if (element['modname'] == 'url'):
            tuple = (element['value'], element['id'])
            result = mssql.execute_query(query_url_template, tuple=tuple, commit=True)
        elif (element['modname'] == 'feedback'):
            tuple = (element['value']['start'], element['value']['end'],
                     element['id'])
            result = mssql.execute_query(query_feedback_template, tuple=tuple, commit=True)
    return result


def append_list_result(csv_row='',
                       category_link='',
                       course_link='',
                       settings_link='',
                       users_link='',
                       grades_link='',
                       report_link='',
                       attendance_link='',
                       errors=''):

    return result_list.append({'csv_row': csv_row,
                               'Category': category_link,
                               'Moodle link of course': course_link,
                               'Link for settings of course': settings_link,
                               'Link for list of participants of course': users_link,
                               'Link for grades': grades_link,
                               'Link for reports (отчёты)': report_link,
                               'Посещаемость': attendance_link,
                               'Errors': errors})


def write_result(result_data):
    f = defs.create_file()
    defs.write_row_to_csv(f, result_data)
    return


def dublicate_course(catid, cid, cfullname, cshortname):
    call = http_request.call
    try:
        newcourse = call('core_course_duplicate_course',
                         categoryid=catid,
                         courseid=cid,
                         fullname=cfullname,
                         shortname=cshortname)
        return newcourse

    except Exception as err:
        if (hasattr(err, 'message')):
            print(err.message)
        else:
            print(err)


def update_course(**kwargs):
    call = http_request.call
    try:
        result = call('core_course_update_courses', courses=[kwargs])
        return result
    except Exception as err:
        if (hasattr(err, 'message')):
            print(err.message)
        else:
            print(err)


def get_category_id(criteria_value, criteria_key='idnumber'):
    call = http_request.call
    result = call('core_course_get_categories', criteria=[
        {'key': criteria_key, 'value': criteria_value}], addsubcategories=0)

    if (len(result) > 0):
        if ('id' in result[0]):
            return result[0]['id']

    return -1


def get_course_id(idnumber):
    call = http_request.call
    if (idnumber != ''):
        result = call('core_course_get_courses_by_field',
                      field='idnumber',
                      value=idnumber)

    if (len(result['courses']) > 0):
        if ('id' in result['courses'][0]):
            return result['courses'][0]['id']

    return -1
