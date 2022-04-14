from calendar import c
import streamlit as st
import os
import csv
import time
import requests
import logging
import re
import copy
import shutil
import base64
import csv
import streamlit.components.v1 as components

from yt_dlp import YoutubeDL
from utils import create_dir, remove_dir
from youtube_transcript_api import YouTubeTranscriptApi
from pydub import AudioSegment

languages_list = (
    "ID (Indonesia)",
    "EN (English)",
)

sample_rate_list = ("16000 Hz", "22050 Hz", "44100 Hz")


def read_generated_metadata_and_audio():
    if "csv_path" in st.session_state and "audio_dir" in st.session_state:
        if st.session_state["csv_path"].endswith(".csv") and os.path.isdir(
            st.session_state["audio_dir"]
        ):
            if len(st.session_state["audio_state"].keys()) == 0:
                st.session_state["current_idx"] = 0
                with open(st.session_state["csv_path"], "r", encoding="utf8") as f:
                    csv_data = csv.reader(f, delimiter=",")
                    next(csv_data)
                    for row in csv_data:
                        st.session_state["audio_state"][row[0]] = {
                            "path": row[1],
                            "sentence": row[2],
                            "sample_rate": row[3],
                            "duration": row[4],
                        }


def generate_dataset_visualization():
    if "audio_state" in st.session_state:
        current_state = st.session_state["audio_state"]
        current_idx = st.session_state["current_idx"]
        len_key = len(list(current_state.keys()))
        if len_key > 0:
            current_key = list(current_state.keys())[current_idx]

        with st.expander("", expanded=True):
            print(current_idx)
            if current_idx >= 0:
                prev_bt, mid, next_bt = st.columns([4, 30, 4])

                next_button = next_bt.button("  Next  ")
                prev_button = prev_bt.button("Previous")

                mid.markdown(
                    f"<center><strong >{current_idx+1}/{len_key}</strong></center>",
                    unsafe_allow_html=True,
                )

                audio_file_path = os.path.join(
                    st.session_state["audio_dir"], current_state[current_key]["path"]
                )
                audio_file = open(audio_file_path, "rb")
                audio_byte = audio_file.read()

                transcript = current_state[current_key]["sentence"]

                st.audio(audio_byte, format="audio/wav")
                text_area = st.text_area(label="", value=transcript)

                _, approve_bt, delete_bt = st.columns([40, 8, 8])
                if approve_bt.button("✅ Approve"):
                    st.session_state["audio_state"][current_key]["sentence"] = text_area

                    st.session_state["audio_approve"].append(current_state[current_key])
                    del st.session_state["audio_state"][current_key]
                    if st.session_state["current_idx"] == len_key - 1:
                        st.session_state["current_idx"] -= 1
                    st.experimental_rerun()

                if delete_bt.button("❌ Delete"):
                    del st.session_state["audio_state"][current_key]
                    if st.session_state["current_idx"] == len_key - 1:
                        st.session_state["current_idx"] -= 1
                    st.experimental_rerun()

                if next_button:
                    st.session_state["audio_state"][current_key]["sentence"] = text_area
                    st.session_state["current_idx"] += 1
                    if st.session_state["current_idx"] > len_key - 1:
                        st.session_state["current_idx"] = len_key - 1
                    st.experimental_rerun()

                if prev_button:
                    st.session_state["audio_state"][current_key]["sentence"] = text_area
                    st.session_state["current_idx"] -= 1
                    if st.session_state["current_idx"] < 0:
                        st.session_state["current_idx"] = 0
                    st.experimental_rerun()
            else:
                print(st.session_state["current_idx"])

        c1, c2 = st.columns(2)

        if c1.button("✅ Approve All "):
            for key in current_state.copy():
                st.session_state["audio_approve"].append(current_state[key])
                del st.session_state["audio_state"][key]
            st.session_state["current_idx"] = -1
            st.experimental_rerun()

        if c2.button("⏬ Generate Dataset"):
            generate_dataset()
            with st.expander("", expanded=True):
                video_id = st.session_state["video_id"]
                with open(st.session_state["audio_zip_path"], "rb") as f:
                    st.download_button(
                        "Download Dataset", f, file_name=f"{video_id}.zip"
                    )


def generate_dataset():
    video_id = st.session_state["video_id"]
    temp_download_dir = os.path.join("temp", "download_dir")
    temp_zip_dir = os.path.join("temp", "zip")
    temp_zip_path = os.path.join(temp_zip_dir, f"{video_id}")

    temp_download_audio_dir = os.path.join(temp_download_dir, "audio")
    temp_download_metadata_path = os.path.join(temp_download_dir, "metadata.csv")

    remove_dir(temp_download_dir)
    remove_dir(temp_zip_dir)

    create_dir(temp_zip_dir)
    create_dir(temp_download_dir)
    create_dir(temp_download_audio_dir)

    for audio_state in st.session_state["audio_approve"]:
        audio_filename = audio_state["path"]
        audio_src = os.path.join(st.session_state["audio_dir"], audio_filename)
        audio_dst = os.path.join(temp_download_audio_dir, audio_filename)
        shutil.copy(audio_src, audio_dst)

    with open(temp_download_metadata_path, "w", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=",")
        fieldnames = ["id"] + list(st.session_state["audio_approve"][0].keys())
        writer.writerow(fieldnames)

        for i, audio_state in enumerate(st.session_state["audio_approve"]):
            data_row = [i] + [audio_state[key] for key in audio_state.keys()]
            writer.writerow(data_row)

    shutil.make_archive(temp_zip_path, "zip", temp_download_dir)
    st.session_state["audio_zip_path"] = f"{temp_zip_path}.zip"


def main():
    # title
    st.markdown(
        "<h1 style='text-align: center; color: grey;'>🌝 Youtube STT Downloader 🌚</h1>",
        unsafe_allow_html=True,
    )

    # youtube link form
    with st.form("video_form"):
        video_id = st.text_input(
            "Youtube ID, Example: https://www.youtube.com/watch?v=D5hnYW5lBuw",
            value="lRsB0ft00sE&t=12s",
        )

        col1, col2 = st.columns(2)
        with col1:
            languages_sb = st.selectbox("Language", languages_list)
        with col2:
            samplerate_sb = st.selectbox("Sample Rate", sample_rate_list)

        my_bar = st.progress(0)
        submitted = st.form_submit_button("Generate")

        def bar_hook(d):
            if d["status"] == "finished":
                my_bar.progress(80)
            if d["status"] == "downloading":
                p = d["_percent_str"].split("%")[0].replace(" ", "")
                p = int(float(p[7:]) * 0.8)

                my_bar.progress(p)
                print(d["filename"], d["_percent_str"], d["_eta_str"])

        if submitted:
            st.session_state["audio_state"] = {}
            st.session_state["audio_approve"] = []
            st.session_state["video_id"] = video_id

            yt_link = f"https://www.youtube.com/watch?v={video_id}"

            language_code = languages_sb.split(" ")[0].lower()
            sample_rate = int(samplerate_sb.split(" ")[0])

            dataset_temp_dir = os.path.join("temp", f"{video_id}_{language_code}")
            audio_temp_dir = os.path.join(dataset_temp_dir, "audio")
            csv_temp_dir = os.path.join(dataset_temp_dir, "metadata.csv")

            # create temp dir
            create_dir("temp")
            create_dir(dataset_temp_dir)
            create_dir(audio_temp_dir)

            try:
                # download raw audio
                ydl_opts = {
                    "format": "bestaudio",
                    "progress_hooks": [bar_hook],
                    "quiet": True,
                    "noplaylist": True,
                    "outtmpl": dataset_temp_dir + "/%(title)s.%(ext)s",
                }
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(yt_link)
                    audio_raw_path = info["requested_downloads"][0]["filepath"]

                # download subtitle
                subtitle = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=[language_code]
                )
                my_bar.progress(90)

                # split audio based on subtitle timestamp
                audio = AudioSegment.from_file(audio_raw_path, frame_rate=sample_rate)
                audio_transcript_list = []
                for i, sub in enumerate(subtitle):
                    audio_id = f"YT_{video_id}_{i}"
                    audio_filename = f"{audio_id}.wav"

                    segment_start = int(sub["start"] * 1000)
                    segment_end = int((sub["start"] + sub["duration"] + 0.3) * 1000)
                    audio_segment = audio[segment_start:segment_end]
                    audio_segment.export(
                        os.path.join(audio_temp_dir, audio_filename), format="wav"
                    )
                    audio_transcript_list.append(
                        {
                            "id": i,
                            "path": audio_filename,
                            "sentence": sub["text"],
                            "sample_rate": sample_rate,
                            "duration": sub["duration"],
                        }
                    )
                # generate metadata
                with open(csv_temp_dir, "w", encoding="utf8") as f:
                    fieldnames = list(audio_transcript_list[0].keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(audio_transcript_list)

                my_bar.progress(100)
                st.session_state["audio_dir"] = audio_temp_dir
                st.session_state["csv_path"] = csv_temp_dir
                read_generated_metadata_and_audio()

            except:
                st.error("Failed Download Audio From Youtube!")

    process_state = False
    # process_button = st.button("Process")
    # if st.button("Process"):
    #     st.session_state["audio_dir"] = "result/audio"
    #     st.session_state["csv_path"] = "result/transcript.csv"

    generate_dataset_visualization()


if __name__ == "__main__":
    main()
