# routes.py

from app import app
from flask import render_template, request
from app_utils import data_init
import route_functions

# -------------------------------------
# Routes
# -------------------------------------

@app.route("/", methods=["GET", "POST"])
def route_dashboard():
    if request.method == 'POST':
        return route_functions.dashboard(request.form)
    else:
        return route_functions.dashboard()


@app.route("/refresh", methods=["GET", "POST"])
def route_refresh():
    if request.method == 'POST':
        # Brings caching param        
        return route_functions.dashboard(request.form)
    else:
        # Same as / GET
        return route_functions.dashboard()


@app.route("/artist/<artist_id>")
def route_artist(artist_id):
    return route_functions.dashboard({"artist_id": artist_id})


@app.errorhandler(404)
def page_not_found():
    data = data_init(app.config)
    data["page"] = "Error"
    return render_template("error.html", data=data), 404
