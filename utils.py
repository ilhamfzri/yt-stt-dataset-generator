import shutil
import os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os


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
