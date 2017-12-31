# air_gallery_lib.py
# Model for reading the Airtable Art database
# An airtable wrapper library wrapper

from airtable import Airtable
import os
import pickle
import logging


class AirGallery:
    _base_key = None
    _api_key = None

    artists_id_to_name = {}

    def __init__(self, use_live_connect=True, base_path="./"):
        self.use_live_connect = use_live_connect
        self.live_backup = True
        self.base_path = base_path

        self.artist_rows = None
        self.collection_rows = None
        self.list_genres = None
        self.artists_by_genre = None
  
        # Look for keys in environment
        self._base_key = os.getenv('AIRTABLE_APP_KEY')
        if self._base_key is None:
            logging.error("air_gallery_lib Fail, APP key is missing")
            return

        self._api_key = os.getenv('AIRTABLE_API_KEY')
        if self._api_key is None:
            logging.error("air_gallery_lib Fail, API key is missing")
            return

        if self.use_live_connect:
            try:
                self.artist_rows = self._pull_live_table("Artists")
                self.collection_rows = self._pull_live_table("Collections")
            except Exception as e:
                logging.error("air_gallery_lib Fail cannot use_live_connect", e.args[0])
                exit()

            if self.live_backup:
                try:
                    self._save_file_table(self.base_path, "Artists", self.artist_rows)
                    self._save_file_table(self.base_path, "Collections", self.collection_rows)
                except Exception as e:
                    logging.error("air_gallery_lib Fail cannot live_backup", e.args[0])
                    exit()

        else:
            try:
                self.artist_rows = self._pull_file_table(self.base_path, "Artists")
                self.collection_rows = self._pull_file_table(self.base_path, "Collections")
            except Exception as e:
                logging.error("air_gallery_lib Fail cannot pull backup", e.args[0])
                exit()

        # Build the rest at load time.
        # Artists table
        self.artists_id_to_name = self._build_artists_id_to_name()
        self.artists_by_id = self._build_artists_by_id()

        # Genres
        self.list_genres = self._build_genres()

        # Collections table
        self.collections_id_to_name = self._build_collections_id_to_name()

    # Public ----------------
    def get_artists_by_id(self):
        return self.artists_by_id

    def get_artists_by_genre(self, genre):
        # just filter all artists
        new_dic = {}
        for artist_id, dic in self.artists_by_id.items():
            if genre in dic["fields"]["Genre"]:
                new_dic[artist_id] = dic
        return new_dic

    def get_artist(self, artist_id):
        return self.artists_by_id[artist_id]

    def get_artists_id_to_name(self):
        return self.artists_id_to_name

    def get_genres(self):
        return self.list_genres

    def get_collections_id_to_name(self):
        return self.collections_id_to_name

    def get_collections(self):
        ar = []
        for row in self.collection_rows:
            ar.append({"id": row["id"], "Name": row["fields"]["Name"]})
        return ar

    def get_artists_in_collection(self, find_collection_id):
        find_coll_artist_ids = None
        for row in self.collection_rows:
            if row["id"] == find_collection_id:
                find_coll_artist_ids = row["fields"]["Artists"]
            else:
                continue
        if find_coll_artist_ids is None:
            return {}  # Id not found, should never happen

        # just filter all artists
        new_dic = {}
        for artist_id, dic in self.artists_by_id.items():
            if artist_id in find_coll_artist_ids:
                new_dic[artist_id] = dic
        return new_dic

    def get_artists_group_by_collection(self):
        # {"Sculpture": {collection_id: 123, artists: [{artist_id: 123, artist_name: "Bob"}, {artist_id ..
        dic = {}
        for row in self.collection_rows:
            ar = []
            for artist_id in row["fields"]["Artists"]:
                adic = {"artist_id": artist_id, "artist_name": self.artists_id_to_name[artist_id]}
                ar.append(adic)
            dic[row["fields"]["Name"]] = {"collection_id": row["id"], "artists": ar}
        return dic

    def get_collections_by_artist(self, find_artist_id):
        # pass artist_id
        # return list of collections
        ar = []
        for row in self.collection_rows:
            for artist_id in row["fields"]["Artists"]:
                if artist_id == find_artist_id:
                    ar.append(row["fields"]["name"])
        return ar

    # Private ---------------

    def _connect(self, table_name):
        conn = Airtable(self._base_key, table_name, api_key=self._api_key)
        return conn

    # Return dict { 123: "Bob", 382: 'Joe',  ... } Sorted by name
    def _build_artists_id_to_name(self):
        dic = {}
        for row in self.artist_rows:
            dic[row["id"]] = row["fields"]["Name"]

        # tricky sort by value. Wait, makes an array of arrays!
        sort_by_val = [(k, dic[k]) for k in sorted(dic, key=dic.get)]
        # grrr not a dict
        dic2 = {}
        for pair in sort_by_val:
            dic2[pair[0]] = pair[1]
        return dic2

    # from array of dicts
    # [ { id: 123, fields: fields ... },
    # to array of dicts ordered by artist name
    # [ { 123: { id: 123, fields: fields ...}},
    def _build_artists_by_id(self):
        rows = self.artist_rows
        new_dic = {}

        # already ordered by artist name
        lookup_dic = self.artists_id_to_name
        for artist_id, name in lookup_dic.items():  # pycharm warning??
            dic = self._find_artist_row(rows, artist_id)
            new_dic[artist_id] = dic
        return new_dic

    # Return dict { 123: "Bob", 382: 'Joe',  ... } Sorted by name
    def _build_collections_id_to_name(self):
        dic = {}
        for row in self.collection_rows:
            dic[row["id"]] = row["fields"]["Name"]

        # tricky sort by value. Wait, makes an array of arrays!
        sort_by_val = [(k, dic[k]) for k in sorted(dic, key=dic.get)]
        # grrr not a dict
        dic2 = {}
        for pair in sort_by_val:
            dic2[pair[0]] = pair[1]
        return dic2

    @staticmethod
    def _find_artist_row(rows, artist_id):
        for dic in rows:
            if dic["id"] == artist_id:
                return dic
        return {}  # should never happen  FIXME error??

    def _build_genres(self):
        # ["dogs", "cats", ...
        list_genres = []
        for row in self.artist_rows:
            # Add genre to list if missing...
            for genre in row["fields"]["Genre"]:
                if genre not in list_genres:
                    list_genres.append(genre)

        list_genres = sorted(list_genres)
        return list_genres

    def _pull_live_table(self, table_name):
        conn = Airtable(self._base_key, table_name, api_key=self._api_key)
        return conn.get_all()

    # Caching data structures
    @staticmethod
    def _pull_file_table(path, table_name):
        pickle_in = open(path + table_name + ".pickle", "rb")
        data = pickle.load(pickle_in)
        pickle_in.close()
        return data

    @staticmethod
    def _save_file_table(path, table_name, data):
        pickle_out = open(path + table_name + ".pickle", "wb")
        pickle.dump(data, pickle_out)
        pickle_out.close()
