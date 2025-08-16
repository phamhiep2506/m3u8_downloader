#!/usr/bin/env python

import cloudscraper
import m3u8
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.utils import parse_header_links
from tqdm import tqdm
import argparse
import shutil
import ffmpeg

URL_M3U8 = ""
LIST_DOWNLOAD_FILES = []
MAX_WORKERS = 0
DIR_DOWNLOAD_TS = ""
MERGE_FILE = ""


def data_to_file(data, file_name):

    if not os.path.exists(DIR_DOWNLOAD_TS):
        try:
            os.mkdir(DIR_DOWNLOAD_TS)
        except Exception as error:
            print(f"Create directory ts: {error}")

    try:
        with open(f"{DIR_DOWNLOAD_TS}/{file_name}", "wb") as f:
            f.write(data)
            f.close()
    except Exception as error:
        print(f"Data to file: {error}")


def png_to_ts(data, file_name):
    data_hex = re.sub(r"^[A-Za-z0-9].*44ae4260", "", data.hex())
    data_byte = bytes.fromhex(data_hex)
    data_to_file(data_byte, file_name)


def merge_ts(file_name):
    with open(MERGE_FILE, "a") as f:
        f.write(f"file ts/{file_name}\n")
        f.close()


def download_ts(url, file_name):
    if os.path.exists(f"{DIR_DOWNLOAD_TS}/{file_name}"):
        return

    try:
        scraper = cloudscraper.create_scraper()
        data = scraper.get(url)
        png_to_ts(data.content, file_name)
    except Exception as error:
        print(f"Download ts: {error}")


def download_multiple_files(urls_ts):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(download_ts, url, file_name) for url, file_name in urls_ts
        ]

        with tqdm(
            total=len(futures),
            desc="Downloading files",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
        ) as progress_bar:
            for future in as_completed(futures):
                try:
                    progress_bar.update(1)
                except Exception as error:
                    print(f"Download multiple files: {error}")
                    print(future)


def ffmpeg_concat_ts(merge_file, output):
    ffmpeg.input(merge_file, format="concat", safe=0).output(output, c="copy").run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="The program downloads ts from m3u8 link and converts png ts to ts file"
    )
    parser.add_argument(
        "-i", "--input", type=str, help="Link download file m3u8", required=True
    )
    parser.add_argument(
        "-n",
        "--new",
        action="store_true",
        help="Download new data",
    )
    parser.add_argument(
        "-w",
        "--worker",
        type=int,
        help="Maximum number of workers when downloading files",
        default=5,
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Path and file name when converting to mp4",
        required=True,
    )
    args = parser.parse_args()

    URL_M3U8 = args.input
    MAX_WORKERS = args.worker
    output_file_name = os.path.basename(args.output).split("/")[-1]
    MERGE_FILE = f"{os.path.splitext(output_file_name)[0]}_merge.txt"
    DIR_DOWNLOAD_TS = f"{os.path.splitext(output_file_name)[0]}_ts"

    if os.path.exists(MERGE_FILE):
        try:
            os.remove(MERGE_FILE)
        except Exception as error:
            print(f"Remove file {MERGE_FILE}: {error}")

    if args.new:
        if os.path.exists(DIR_DOWNLOAD_TS):
            try:
                shutil.rmtree(DIR_DOWNLOAD_TS)
            except Exception as error:
                print(f"Remove directory ts: {error}")

    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(URL_M3U8)

        playlist = m3u8.loads(f"{response.text}")

        for index, url in enumerate(playlist.segments.uri):
            LIST_DOWNLOAD_FILES.append((url, f"{index}.ts"))
            merge_ts(f"{index}.ts")
    except Exception as error:
        print(f"Get M3U8: {error}")

    download_multiple_files(LIST_DOWNLOAD_FILES)

    ffmpeg_concat_ts(MERGE_FILE, args.output)
