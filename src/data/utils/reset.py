import configparser

from shutil import move
from os import remove
from os.path import exists
import sqlite3

from ..schema import \
CREATE_TABLE_PRICE_HISTORY_DAY, \
CREATE_TABLE_PRICE_HISTORY_HOUR, \
CREATE_TABLE_PRICE_HISTORY_MINUTE, \
CREATE_TABLE_STOCK_INDICES, \
transfer_table

# ----------------------------------- admin ---------------------------------- #
config = configparser.ConfigParser()
with open('config.ini') as f:
    config.read_file(f)

PROJECT_DB_PATH = config['DB Path']['PROJECT_DB_PATH']
PROJECT_DB_PATH_TEMP = config['DB Path']['PROJECT_DB_PATH_TEMP']
TRADELOG_PATH = config['XML Paths']['TRADELOG_PATH']
TRADELOG_BACKUP_PATH = config['Backup Paths']['TRADELOG_BACKUP_PATH']
DIVIDEND_HISTORY_BACKUP_PATH = config['Backup Paths']['DIVIDED_HISTORY_BACKUP_PATH']
DIVIDEND_HISTORY_PATH = config['XML Paths']['DIVIDEND_HISTORY_PATH']
# ---------------------------------------------------------------------------- #

def reset_datastore():
    """
    Equivalent to a "destroy script" - does a couple of things
    1. Moves all downloaded data to backup folder (e.g. store/historic -> store/backups)
    2. Migrates price history tables from current database to a temporary database
    3. Deletes current database

    Why bother? Saves time deleting files during developing/testing, and also
    allows the price history data downloaded from IB to be preserved over time
    (slowly removing issue of IB API being slow)

    ** This assumes that the schema for the transferred tables do not change (it shouldn't)
    """ 

    # ---------------------------------- Step 1 ---------------------------------- #
    print('Removing the tradelog and dividend history raw downloads... \n') # convert to log
    if exists(TRADELOG_PATH):
        move(TRADELOG_PATH, TRADELOG_BACKUP_PATH)

    if exists(DIVIDEND_HISTORY_PATH):
        move(DIVIDEND_HISTORY_PATH, DIVIDEND_HISTORY_BACKUP_PATH)
    # ---------------------------------------------------------------------------- #

    # ---------------------------------- Step 2 ---------------------------------- #
    if exists(PROJECT_DB_PATH_TEMP):
        remove(PROJECT_DB_PATH_TEMP)

    print('Creating the temporary history database ... \n') # convert to log
    temp_db_conn = sqlite3.connect(PROJECT_DB_PATH_TEMP)
    temp_db_c = temp_db_conn.cursor()
    temp_db_c.execute(CREATE_TABLE_PRICE_HISTORY_DAY)
    temp_db_c.execute(CREATE_TABLE_PRICE_HISTORY_HOUR)
    temp_db_c.execute(CREATE_TABLE_PRICE_HISTORY_MINUTE)
    temp_db_c.execute(CREATE_TABLE_STOCK_INDICES)
    temp_db_conn.commit()

    print('Copying over historic data from current database ... \n') # convert to log
    db_conn = sqlite3.connect(PROJECT_DB_PATH)
    db_c = db_conn.cursor()
    db_c.execute("""
        ATTACH DATABASE '{temp_db_path}' AS other;
        """.format(temp_db_path=PROJECT_DB_PATH_TEMP)
    )

    transfer_table(db_c, 'Price_History_Day')
    transfer_table(db_c, 'Price_History_Hour')
    transfer_table(db_c, 'Price_History_Minute')
    transfer_table(db_c, 'Stock_Indices')

    db_conn.commit()
    # ---------------------------------------------------------------------------- #

    # ---------------------------------- Step 3 ---------------------------------- #
    print('Removing current database ... \n') # convert to log
    remove(PROJECT_DB_PATH)
    # ---------------------------------------------------------------------------- #
