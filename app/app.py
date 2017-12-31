# Airtable Gallery app

# Usage: Run on localhost
"""
cd ~/titan/airtable_gallery
workon airtable_gallery
export FLASK_APP=app/app.py
export AIRTABLE_APP_KEY=app11111
export AIRTABLE_API_KEY=key11111
export WHERE_RUNNING=localhost
export FLASK_DEBUG=true
flask run -p 3000
"""

from flask import Flask
import logging
import app_utils
import sys

app = Flask(__name__, static_folder='assets')

# set the secret key for sessions
# app.secret_key = os.urandom(24)
# For sessions, used os.urandom(24)
app.secret_key = b'\xc8_._|a\x89\xed\x7f\xfa\xec\xdd\x02\x9aT\xcc\x01\x87\xc2\xd3\xdb\xfa\xffg'
import routes  # app dependency, must be after Flask

setting_err = app_utils.load_settings(app)  # type: str
if setting_err:
    logging.error(setting_err)
    sys.exit()

logging.basicConfig(filename='app.log', level=logging.INFO)
logging.info('---Starting flask app')


# -------------------------------------
# Another way to run:
# -------------------------------------
if __name__ == '__main__':
    # Doesn't get here at pythonanywhere, because file is imported by WSGI
    #   https://help.pythonanywhere.com/pages/Flask 
    if app.config["APP_SETTINGS_LEVEL"] == 'production':
        app.run(debug=False)
    else:
        app.run(debug=True)
