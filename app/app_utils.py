# app_utils.py
#  General utils

from os import getenv
from datetime import datetime


# Load configuration at program initialization
def load_settings(app):
    settings_path = "settings/"
    app.config.from_pyfile(settings_path + "default.cfg")

    # Which server is this?
    where_running = getenv('WHERE_RUNNING')
    if where_running == 'localhost':
        app.config.from_pyfile(settings_path + "localhost.cfg")
    elif where_running == 'pythonanywhere':
        app.config.from_pyfile(settings_path + "pythonanywhere.cfg")
    else:
        return "Error - load_settings(): cannot load settings"
    return ""


# Init template data dict
def data_init(app_config):

    now = datetime.now()
    data = { 
        "current_year": now.year,
        "moneysym": "$",
        "breadcrumb_fifo": []
        }
    if app_config:
        data["app_name"] = app_config["APP_NAME"]
        data["app_motto"] = app_config["APP_MOTTO"]
    return data
