#!/usr/bin/env python

import argparse
import glob
import m3u8
from tqdm import tqdm
import requests
import os
import re
import subprocess


REGEX_PNG = r"^[A-Za-z0-9].*44ae4260"


def get_urls_inside_m3u8(url: str, referer: str) -> list[str]:
    response = requests.get(url, headers={"Referer": referer}, stream=True)
    playlist = m3u8.loads(response.text)
    return playlist.files


def png_to_ts(path_to_file_ts: str):
    hex_string = subprocess.run(
        ["xxd", "-ps", "-c", "0", path_to_file_ts], capture_output=True
    )
    hex_string_remove_png = re.sub(REGEX_PNG, "", hex_string.stdout.decode("utf-8"))
    data = subprocess.run(
        ["xxd", "-ps", "-r"], input=hex_string_remove_png.encode(), capture_output=True
    )

    os.remove(path_to_file_ts)

    with open(path_to_file_ts, "wb") as file:
        file.write(data.stdout)
    file.close()


def download_ts(url: str, referer: str, name_ts: str, output_path: str):
    if os.path.exists(f"{output_path}/{name_ts}.ts") is True:
        return

    with requests.get(url, headers={"Referer": referer}, stream=True) as response:
        response.raise_for_status()
        with open(f"{output_path}/{name_ts}.ts", "wb") as file:
            for chuck in response.iter_content(chunk_size=1024):
                if chuck:
                    file.write(chuck)
    file.close()

    png_to_ts(f"{output_path}/{name_ts}.ts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="Input url m3u8", required=True)
    parser.add_argument("-r", "--referer", help="Referer url", required=False)
    parser.add_argument(
        "-c",
        "--continued",
        action="store_true",
        help="Continue downloading",
        required=False,
    )
    parser.add_argument("-o", "--output", help="/path/to/file.mp4", required=True)
    args = parser.parse_args()

    urls = get_urls_inside_m3u8(args.input, args.referer)

    dir_output_ts = "ts"
    file_merge = "merge.txt"

    if args.continued is False:
        if not os.path.exists(dir_output_ts):
            os.mkdir(dir_output_ts)

        ts_files = glob.glob(f"{dir_output_ts}/*")
        for file in ts_files:
            os.remove(file)

    with open(file_merge, "w") as file:
        for index, url in enumerate(tqdm(urls)):
            download_ts(url, args.referer, str(index), dir_output_ts)
            file.write(f"file {dir_output_ts}/{index}.ts\n")
    file.close()

    os.system(f"ffmpeg -f concat -i merge.txt -c copy {args.output}")
