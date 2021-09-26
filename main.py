import os
import shutil
import sys
import time
from argparse import ArgumentParser

import cv2
import ffmpeg
import pydub
from colorama import Fore, init
from pexecute.thread import ThreadLoom
from wand.image import Image

init(True)
def cache():
    dirs_ = [
        "work",
        "work/in",
        "work/out"
    ]
    for i in dirs_:
        if os.path.isdir(i):
            print(Fore.GREEN + f"[Cache] Re-Creating dir '{i}'")
            shutil.rmtree(i)
            os.mkdir(i)
        else:
            print(Fore.GREEN + f"[Cache] Creating dir '{i}'")
            os.mkdir(i)
    
def distort(inp: str, out: str, frap: int):
    img = Image(filename=inp)
    x, y = img.size[0], img.size[1]
    popx = int(50*(x//100))
    popy = int(50*(y//100))
    img.liquid_rescale(popx, popy, delta_x=1, rigidity=0)
    img.resize(x, y)
    img.save(filename=out)

def main(args):
    cache()
    i = args.i
    if not os.path.isfile(i):
        print(Fore.RED + "[Main] Video not found!")
        sys.exit(1)
    v = cv2.VideoCapture(i)
    fps = v.get(cv2.CAP_PROP_FPS)
    frames_total = int(v.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(v.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(v.get(cv2.CAP_PROP_FRAME_HEIGHT))
    bitrate = v.get(cv2.CAP_PROP_BITRATE)
    print(Fore.CYAN + f"[Video info] Size: {width}x{height}")
    print(Fore.CYAN + f"[Video info] FPS: {fps}")
    print(Fore.CYAN + f"[Video info] Total frames: {frames_total}")
    print(Fore.CYAN + f"[Video info] Bitrate: {bitrate}")
    print(Fore.BLUE + "[Worker] Starting process...")
    start_time = time.time()
    print(Fore.BLUE + "[Worker] Decomposing the video into frames via opencv...")
    f = 1
    while True:
        if v.grab():
            _, frame = v.retrieve()
            cv2.imwrite(f"work/in/{str(f).zfill(8)}.png", frame)
            f += 1
        else: break
    print(Fore.BLUE + "[Worker] Distorting fraps via imagemagick...")
    loom = ThreadLoom(max_runner_cap=args.t)
    for i in range(frames_total):
        loom.add_function(distort, [f"work/in/{str(i+1).zfill(8)}.png", f"work/out/{str(i).zfill(8)}.png", i])
    loom.execute()
    print(Fore.BLUE + "[Worker] Exporting audio via ffmpeg...")
    a = pydub.AudioSegment.from_file(args.i)
    a.export("work/audio.mp3")
    print(Fore.BLUE + "[Worker] Exporting video via ffmpeg...")
    (
        ffmpeg
        .input("work/out/*.png", pattern_type='glob', framerate=fps, pix_fmt='yuv420p')
        .output("work/temp.mp4")
        .global_args('-loglevel', 'quiet')
        .overwrite_output()
        .run(overwrite_output=True)
    )
    i_vid = ffmpeg.input("work/temp.mp4")
    i_aud = ffmpeg.input("work/audio.mp3")
    (
        ffmpeg
        .concat(i_vid, i_aud, v=1, a=1)
        .output(args.o)
        .global_args('-loglevel', 'quiet')
        .overwrite_output()
        .run(overwrite_output=True)
    )
    end = time.time()-start_time
    total_time = time.strftime('%Mm:%Ss', time.gmtime(end))
    print(Fore.GREEN + f"[Finish] Distorted successful! Time: {total_time}")
        
    

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-i', type=str, required=True,  help='Input videopath/file')
    parser.add_argument('-t', type=int, required=False, help='Threads [default 5]', default=5)
    parser.add_argument('-o', type=str, required=False, help='Output filepath/name', default="out.mp4")
    args = parser.parse_args()
    main(args)
    
    
