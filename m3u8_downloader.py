#!/usr/bin/env python

import cloudscraper
import m3u8
import re
import os
from tqdm import tqdm
import concurrent.futures

URL_M3U8 = "https://stream.cliphot69.one/video2/85e9c82a-05df-4946-a00e-97736b38b94a/master.html"


def data_to_file(data, file_name):

    if not os.path.exists("ts"):
        try:
            os.mkdir("ts")
        except Exception as error:
            print(error)

    try:
        with open(f"ts/{file_name}", "wb") as f:
            f.write(data)
            f.close()
    except Exception as error:
        print(error)


def png_to_ts(data, file_name):
    data_hex = re.sub(r"^[A-Za-z0-9].*44ae4260", "", data.hex())
    data_byte = bytes.fromhex(data_hex)
    data_to_file(data_byte, file_name)


def merge_ts(file_name):
    with open("merge.txt", "a") as f:
        f.write(f"file ts/{file_name}\n")
        f.close()


threads = []
try:
    scraper = cloudscraper.create_scraper()
    response = scraper.get(URL_M3U8)

    playlist = m3u8.loads(f"{response.text}")

    for index, url in enumerate(
        tqdm(playlist.segments.uri, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}")
    ):
        if os.path.exists(f"ts/{index}.ts"):
            continue

        try:
            data = scraper.get(f"{url}")
            png_to_ts(data.content, f"{index}.ts")
            merge_ts(f"{index}.ts")
        except Exception as error:
            print(error)

except Exception as error:
    print(error)
