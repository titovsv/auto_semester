
from tabulate import tabulate
import csv
import defs
import http_request
import config                                                     

result_list = list()

def help():
    
    bcolors = defs.bcolors
    defs.clear_console()
    print_ext = defs.print_ext

    print("---Stat document---\n")
    print_ext("Usage script functions", "header")
    print_ext("First of all run python cli and import moodle", "bold")

    print(f"{bcolors.BOLD}moodle.call{bcolors.ENDC}(function_name, args) - call web service function from command line")
    print(
        "Example args: 'core_course_update_courses',courses = [{'id': 1, 'fullname': 'My favorite course'}]")
    print("(called funcrion must be included in web service functions)")
    print("\n")

    print(f"{bcolors.BOLD}moodle.create_semester(){bcolors.ENDC} - call function to create categories.\
    You should prepare csv file for script.\nScript displays some hints")
    print_ext('Example csv file: link to file', 'ok')
    print("---End of document---\n")


def create_categories(name='', idnumber='', parent='', visible='1'):

    try:
        newCategories = http_request.call('core_course_create_categories', categories=[
                             {'name': name, 'parent': parent, 'idnumber': idnumber}])
        return newCategories
    except Exception as err:
        if hasattr(err, 'message'):
            print(err.message)
        else:
            print(err)


def create_semester():

    defs.clear_console()

    bcolors = defs.bcolors
    print_ext = defs.print_ext
    
    pathtofile = input(
        f"{bcolors.WARNING}Input path to csv file with data: {bcolors.ENDC}")
    defs.clear_console()
    try:
        csvfile = open(pathtofile, newline='', encoding='utf-8-sig')
    except FileNotFoundError as err:
        print(f"File {pathtofile} not found!")
        return
    except PermissionError:
        print(f"Insufficient permission to read {pathtofile}!")
        return
    except IsADirectoryError:
        print(f"{pathtofile} is a directory!")
        return
    csv_data = list(csv.DictReader(csvfile, delimiter=";"))

    ##Display user csv file content
    l = list()

    for row in csv_data:
        l.append([i for i in row.values()])

    print('Data from csv file:\n')
    print(f"{bcolors.HEADER}")
    print(tabulate(l, headers=csv_data[0].keys(), tablefmt='orgtbl'))
    print(f"{bcolors.ENDC}", "\n")

    user_input = input(
        "Check printed data', Is it Ok? 'Y' to continue, 'N' to abort: ")

    if user_input.lower() not in ["y", "n"]:
        print(f"{bcolors.FAIL}Unknown input start again{bcolors.ENDC}")
        return

    if user_input.lower() == "n":
        print('User aborted')
        return
    defs.clear_console()
    print_ext('Creating categories in moodle...', 'warning')

    i = 1

    for row in csv_data:

        if row['cat_name'] == '' and row['course_template'] == '':
            append_list_result(csvrow=i, errors='Rows cat_name and course_template is reqired')
            i += 1
            continue

        updatecourse = False

        if row['cat_name'] != '':
            category_name = row['cat_name']
        elif row['cat_name'] == '' and category_name:
            print('')
        else:
            print_ext('Category name is reqired', 'fail')
            append_list_result(csvrow=i, errors='Category name is reqired')
            i += 1
            continue

        if row['cat_idnumber'] != '':
            category_idnumber = row['cat_idnumber']
        elif row['cat_name'] == '' and category_idnumber:
            print('')
        else:
            print_ext('Category idnumber is reqired', 'fail')
            append_list_result(csvrow=i, errors='Category idnumber is reqired')
            i += 1
            continue
        
        if row['parent_idnumber'] != '':
            parent = row['parent_idnumber']
        elif row['cat_name'] == '' and parent:
            print('')
        else:
            print_ext('Category parent_idnumber is reqired', 'fail')
            append_list_result(csvrow=i, errors='Category parent_idnumber is reqired')
            i += 1
            continue

        ###for result
        new_cat = ''
        new_course = ''

        if parent == 0 or parent == "0":
            category_parent = 0
        else:
            category_parent = get_category_id(criteriaValue=parent)

        if(category_parent < 0):
            append_list_result(csvrow=i, errors="No parent category with idnumber " + row['parent_idnumber'])
            #result_list.append({'CsvRow' : i ,'Category': '-', 'Course': '-', 'Errors': "No parent category with idnumber " + row['parent_idnumber'] })
            i += 1
            continue
        
        result = get_category_id(criteriaValue=category_idnumber)
        
        if isinstance(result, int) and result < 0:
            result = create_categories(category_name, category_idnumber, category_parent)

            if isinstance(result, list):
                print_ext("Created category with id " + str(result[0]['id']), 'ok')
                new_cat = config.URL + config.CATEGORY_VIEW_ENDPOINT + str(result[0]['id'])
            else:
                print_ext("Error creating category with id " + str(result[0]['id']), 'fail')
                append_list_result(csvrow=i, errors="Error creating category " + str(category_name))
                #result_list.append({'CsvRow' : i ,'Category': '', 'Course': '',  'Errors': "Error creating category " + str(category_name)})
                i += 1
                continue
        else:
            result = [{'id': result}]

        course_template = row['course_template']

        if row['feedback'] != '':
            course_template = row['course_template'] + '_' + row['feedback']

        if course_template != '':

            cid = get_course_id(course_template)

            if cid > 0:
                print_ext("Copy course " +
                      str(course_template) + " to category " + str(category_name), 'warning')
            else:
                append_list_result(csvrow=i, categorylink=new_cat, errors="Course template not found " + str(course_template))
                #result_list.append({'CsvRow' : i, 'Category': new_cat, 'Course': '',  'Errors': "Course template not found " + str(course_template)})
                print_ext("Course template not found " +
                      str(course_template) + ". Check csv row: " + str(i), 'fail')
                i += 1
                continue

            course_category = result[0]['id']
            course_name = row['course_name']
            course_shortname = row['course_shortname']

            duplicate_result = dublicate_course(
                course_category, cid, course_name, course_shortname)

            if isinstance(duplicate_result, dict):
                print_ext("Course duplicated. Id " +
                          str(duplicate_result['id']), 'ok')
                new_course = config.URL + config.COURSE_VIEW_ENDPOINT + str(duplicate_result['id'])
                settings_link = config.URL + config.COURSE_SETTINGS_ENDPOINT + str(duplicate_result['id'])
                users_link = config.URL + config.COURSE_USERS_ENDPOINT + str(duplicate_result['id'])
                grades_link = config.URL + config.COURSE_GRADES_ENDPOINT + str(duplicate_result['id'])
                report_link = config.URL + config.COURSE_REPORTS_ENDPOINT + str(duplicate_result['id'])
                updatecourse = row['course_idnumber'] != ''
            else:
                print_ext("Error duplicate course " +
                          str(course_template) + " For detailes look above", 'fail')
                append_list_result(csvrow=i, categorylink=new_cat, errors='Error duplicate course')
                #result_list.append({'CsvRow': i, 'Category': new_cat, 'Course': new_course,  'Errors': 'Error duplicate course'})
                i += 1
                continue
                

            if updatecourse:
                start=defs.get_timestamp(row['course_start'])
                end=defs.get_timestamp(row['course_end'])
                telegram_chat =  row['telegram_chat']
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

                if row['course_visible'] in 'Yes|yes|1|True|true':
                    course_visible = '1'
                else:
                    course_visible = '0'
                print('Обновление данных курса ' + row['course_idnumber'])
                update_result = update_course(
                    id=duplicate_result['id'], idnumber=row['course_idnumber'], startdate=start, enddate=end, visible=course_visible, summary = summary)
                if update_result['warnings']:
                    print(update_result['warnings'])
                    append_list_result(csvrow=i, categorylink=new_cat, courselink=new_course, settingslink=settings_link, userslink=users_link, gradeslink=grades_link, reportlink=report_link, errors='Course update warnings: ' + str(update_result['warnings']))
                    #result_list.append({'CsvRow': i, 'Category': new_cat, 'Course': new_course,  'Errors': 'Course update warnings: ' + str(update_result['warnings'])})
                else:
                    append_list_result(csvrow=i, categorylink=new_cat, courselink=new_course, settingslink=settings_link, userslink=users_link, gradeslink=grades_link, reportlink=report_link)
                    #result_list.append({'CsvRow': i, 'Category': new_cat, 'Course': new_course,  'Errors': ''})
            else:
                append_list_result(csvrow=i, categorylink=new_cat, courselink=new_course, settingslink=settings_link, userslink=users_link, gradeslink=grades_link, reportlink=report_link)
                #result_list.append({'CsvRow': i, 'Category': new_cat, 'Course': new_course,  'Errors': ''})
        else:
            append_list_result(csvrow=i, categorylink=new_cat)
        i += 1

    write_result(result_list)
    print('Done')

def append_list_result(csvrow = '', categorylink = '', courselink = '', settingslink = '',
                        userslink = '', gradeslink = '', reportlink = '', attendancelink = '', errors = ''):
    
    return result_list.append({'CsvRow': csvrow, 'Category': categorylink, 'Moodle link of course': courselink,
                               'Link for settings of course': settingslink, 'Link for list of participants of course': userslink,
                               'Link for grades': gradeslink, 'Link for reports (отчёты)': reportlink, 'Посещаемость': attendancelink,
                               'Errors': errors})


def write_result(result_data):
    f = defs.create_file()
    defs.write_row_to_csv(f, result_data)
    return

def dublicate_course(catid, cid, cfullname, cshortname):
    call = http_request.call
    try:
        newcourse = call('core_course_duplicate_course', categoryid=catid,
                         courseid=cid, fullname=cfullname, shortname=cshortname)
        return newcourse
    except Exception as err:
        if hasattr(err, 'message'):
            print(err.message)
        else:
            print(err)


def update_course(**kwargs):
    call = http_request.call
    try:
        warnings = call('core_course_update_courses', courses=[kwargs])
        return warnings
    except Exception as err:
        if hasattr(err, 'message'):
            print(err.message)
        else:
            print(err)

def get_category_id(criteriaKey ='idnumber', criteriaValue=''):
    call = http_request.call
    if criteriaValue != '':
        categories = call('core_course_get_categories', criteria=[
                          {'key': criteriaKey, 'value': criteriaValue}])
    else:
        categories = call('core_course_get_categories')
    if categories:
        return categories[0]['id']

    return -1

def get_course_id(idnumber):
    call = http_request.call
    if idnumber != '':
        course_info = call('core_course_get_courses_by_field', field='idnumber', value=idnumber)

    if course_info['courses']:
        return course_info['courses'][0]['id']

    return -1
