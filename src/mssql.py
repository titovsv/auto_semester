import pyodbc
import config as config


def mssql_connect():
    try:
        cnxn = pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};"
                              "Server="+config.MSSQL_SERVER+";"
                              "Database="+config.DB+";"
                              "Trusted_Connection=yes;")
        return cnxn
    except pyodbc.Error as error:
        print(error)
        return False


def execute_query(query, tuple=(), commit=False):


    try:
        cnxn = mssql_connect()
        if (cnxn is False):
            return False
        cursor = cnxn.cursor()
        cursor.execute(query, tuple)
        if (commit):
            cnxn.commit()
        rows = cursor.fetchall()
        return rows
    except pyodbc.Error as error:
        return error
