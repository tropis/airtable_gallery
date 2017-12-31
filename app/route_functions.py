# route_functions.py

from app import app
from flask import render_template, session
from app_utils import data_init

from air_gallery_lib import AirGallery
import random

# - - - - - - - - - - - - - - - - - - -
# Route Functions
# - - - - - - - - - - - - - - - - - - -


def dashboard(params=None):
    msg = ""
    data = data_init(app.config)
    data["page"] = "Dashboard"
    artist_id = ""
    genre = ""
    collection_id = ""

    # Get params from Get, Post, Session
    # Session params used to persist the last artist filter
    # All Artist click disables all filters
    # A home or reset clears filters
    # A reset with live_cached changes Live or Cached session param

    live_cached = session.get("live_cached", "live")  # default

    if params:
        if "genre_filter" in session:
            genre = session["genre_filter"]

        elif "collection_filter" in session:
            collection_id = session["collection_filter"]

        if params.get("genre_filter", ""):
            genre = params["genre_filter"]
            collection_id = ""

        elif params.get("collection_filter", ""):
            collection_id = params["collection_filter"]
            genre = ""

        if params.get("artist_id", ""):
            # Clicked an artist...
            artist_id = params["artist_id"]

        if params.get("live_cached", ""):
            live_cached = params["live_cached"]

    # Reset filters
    session.pop('collection_filter', None)
    session.pop('genre_filter', None)

    # Was live/cached toggled?
    if live_cached:
        session["live_cached"] = live_cached

    # Where to get data from? And mark the radio controls
    if session.get("live_cached", "") == "cached":
        # Pull from pickle files. Set CSS classes.
        air = AirGallery(False)
        data["cached_classes"] = " is-success is-selected "
        data["cached_checked"] = " checked "

    else:
        # Default, pull from Airtable API. Set CSS classes.
        air = AirGallery()
        data["live_classes"] = " is-success is-selected "
        data["live_checked"] = " checked "

    # artists_id_to_name = air.get_artists_id_to_name()
    # artist_ids = list(artists_id_to_name.keys())  # All artists
    collections = air.get_collections_id_to_name()
    genres = air.get_genres()

    # Get artists and Save filter for next time
    data["is-genre_filter"] = ""
    data["is-collection_filter"] = ""
    data["is-all_filter"] = ""
    if genre:
        artists = air.get_artists_by_genre(genre)
        session["genre_filter"] = genre 
        data["is_genre_filter"] = "is-active"

    elif collection_id:
        artists = air.get_artists_in_collection(collection_id)
        session["collection_filter"] = collection_id  
        data["is_collection_filter"] = "is-active"
        data["collection_name"] = collections[collection_id]

    else:
        # No filtering
        artists = air.get_artists_by_id()
        data["is_all_filter"] = "is-active"

    # Get a list of artist IDs from this filter
    limited_artists_ids = list(artists.keys())

    # Pick one artist at random to display
    if artist_id:
        artist = None
        found = False
        for aid, dic in artists.items():
            if dic["id"] == artist_id: 
                found = True
                artist = dic

        if not found:
            # Error, just givem random
            random_id = random.choice(limited_artists_ids)
            artist = artists[random_id]  # 1
            msg = "The artist was not found, selecting a random one"
    else:
        random_id = random.choice(limited_artists_ids)
        artist = artists[random_id]  # 2

    data["artist_name"] = artist["fields"]["Name"]
    data["artist_id"] = artist["id"]
    data["artist_specialty"] = "FIX"
    data["bio"] = artist["fields"]["Bio"]
    data["artist_genres"] = artist["fields"]["Genre"]
    data["collection_ids"] = artist["fields"]["Collection"]

    # Extract the images. Use the same ones for thumbnails
    pic_urls = []
    ix = 1
    for pics in artist["fields"]["Attachments"]:
        pic = pics["thumbnails"]["large"]["url"]
        pic_urls.append({"id": ix, "pic": pic})
        ix += 1
    data["pictures"] = render_template("pictures.html", pic_urls=pic_urls)

    data["name_selector"] = render_template("name_selector.html", 
                                            artists=artists,
                                            genres=genres,
                                            collections=collections,
                                            artist_id=data["artist_id"])
    return render_template("index.html", msg=msg, data=data)
