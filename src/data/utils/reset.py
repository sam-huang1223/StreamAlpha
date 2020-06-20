import configparser

from shutil import move
from os import remove
from os.path import exists

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
    2. Migrates tables from current database to a temporary database

    Why bother? Saves time deleting files during developing/testing, and also
    allows the historical data (e.g. price data downloaded from IB) to be preserved over time
    (slowly removing issue of the IB API being slow)
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

    print('Backing up data from current database ... \n') # convert to log
    if exists(PROJECT_DB_PATH):
        move(PROJECT_DB_PATH, PROJECT_DB_PATH_TEMP)
    # ---------------------------------------------------------------------------- #
