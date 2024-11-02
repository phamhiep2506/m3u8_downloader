#!/usr/bin/env python

import requests
import os
import subprocess
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help = "Input url m3u8")
args = parser.parse_args()

os.system(f"mkdir -p {os.getcwd()}/ts")
os.system(f"rm -rf {os.getcwd()}/ts/*")

os.system(
    f"curl -s {args.input} | grep https > url.txt"
)

merge = open(f"{os.getcwd()}/merge.txt", "w")
with open("url.txt", "r") as file:
    for i, line in enumerate(file):
        print(f"Download {i}.png")

        req = requests.get(line.strip())

        open(f"{os.getcwd()}/ts/{i}.png", "wb").write(req.content)

        xxd_png = "89504e470d0a1a0a0000000d494844520000000100000001010300000025db56ca00000003504c5445000000a77a3dda0000000174524e530040e6d8660000000a4944415408d76360000000020001e221bc330000000049454e44ae4260"
        xxd_ts = subprocess.run(
            f"xxd -ps -c 0 {os.getcwd()}/ts/{i}.png",
            capture_output=True,
            shell=True,
            text=True,
        )
        xxd_ts = xxd_ts.stdout.replace(xxd_png, "")

        open(f"{os.getcwd()}/ts/{i}.temp", "w").write(xxd_ts)

        os.system(f"cat {os.getcwd()}/ts/{i}.temp | xxd -ps -c 0 -r - {os.getcwd()}/ts/{i}.ts")

        merge.write(f"file '{os.getcwd()}/ts/{i}.ts'")
        merge.write("\n")

os.system(f"{os.getcwd()}/ts/*.temp")
os.system(f"{os.getcwd()}/ts/*.png")
os.system(f"ffmpeg -f concat -i {os.getcwd()}/merge.txt -c copy output.mp4")