#!/usr/bin/env python

import requests
import os
import subprocess
import argparse
from tqdm import tqdm


def download_m3u8(args):
    if args.referer is None:
        os.system(f"curl -s {args.input} | grep https > url.txt")
    else:
        os.system(
            f"curl -s -H 'Referer: {args.referer}' {args.input} | grep https > url.txt"
        )


def download_ts(url):
    res = requests.get(url, stream=True)

    total_size = int(res.headers.get("content-length", 0))
    block_size = 1024

    with tqdm(
        total=total_size, unit="B", unit_scale=True, desc=f"{i}.png"
    ) as progress_bar:
        with open(f"{os.getcwd()}/ts/{i}.png", "wb") as file:
            for data in res.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
    if total_size != 0 and progress_bar.n != total_size:
        raise RuntimeError("Could not download file")

    xxd_png = "89504e470d0a1a0a0000000d494844520000000100000001010300000025db56ca00000003504c5445000000a77a3dda0000000174524e530040e6d8660000000a4944415408d76360000000020001e221bc330000000049454e44ae4260"
    xxd_ts = subprocess.run(
        f"xxd -ps -c 0 {os.getcwd()}/ts/{i}.png",
        capture_output=True,
        shell=True,
        text=True,
    )
    xxd_ts = xxd_ts.stdout.replace(xxd_png, "")

    open(f"{os.getcwd()}/ts/{i}.temp", "w").write(xxd_ts)

    os.system(
        f"cat {os.getcwd()}/ts/{i}.temp | xxd -ps -c 0 -r - {os.getcwd()}/ts/{i}.ts"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="Input url m3u8")
    parser.add_argument("-r", "--referer", help="Referer url")
    args = parser.parse_args()

    os.system(f"mkdir -p {os.getcwd()}/ts")
    os.system(f"rm -rf {os.getcwd()}/ts/*")

    download_m3u8(args)

    merge = open(f"{os.getcwd()}/merge.txt", "w")
    with open("url.txt", "r") as file:
        for i, line in enumerate(file):
            merge.write(f"file 'ts/{i}.ts'")
            merge.write("\n")
            download_ts(line.strip())
