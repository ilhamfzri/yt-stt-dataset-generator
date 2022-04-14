import shutil
import os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
from urllib.parse import urlparse, parse_qs
from contextlib import suppress


def get_yt_id(url, ignore_playlist=False):
    if url.startswith("http://") == False:
        url = "http://" + url
    query = urlparse(url)
    if query.hostname == "youtu.be":
        return query.path[1:]
    if query.hostname in {"www.youtube.com", "youtube.com", "music.youtube.com"}:
        if not ignore_playlist:
            # use case: get playlist id not current video in playlist
            with suppress(KeyError):
                return parse_qs(query.query)["list"][0]
        if query.path == "/watch":
            return parse_qs(query.query)["v"][0]
        if query.path[:7] == "/watch/":
            return query.path.split("/")[1]
        if query.path[:7] == "/embed/":
            return query.path.split("/")[2]
        if query.path[:3] == "/v/":
            return query.path.split("/")[2]

    return False


def create_dir(path):
    dir = path
    check = os.path.isdir(dir)

    if not check:
        os.makedirs(dir)


def remove_dir(path):
    try:
        shutil.rmtree(path)
    except:
        pass


def remove_file(path):
    os.remove(path)
