import asyncio
import logging
import os
import re
import subprocess
import sys
import time

import progressbar
from natsort import natsorted

logger = logging.getLogger(__name__)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


def flv_to_mp4(path):
    if not os.path.exists(path):
        sys.stderr.write('File not exists\n')
        sys.stdout.flush()
        return

    sys.stdout.write('Processing...\n')
    sys.stdout.flush()

    # FFMPEG 路径
    file_path = os.path.dirname(__file__)
    ffmpeg_path = file_path + os.sep + 'ffmpeg' + os.sep + 'bin' + os.sep + 'ffmpeg.exe'  # 这里替换成自己的ffmpeg路径

    sys.stdout.write('Scanning file(s)...')
    sys.stdout.flush()

    # 获取所有flv文件
    file_list = []
    if os.path.isdir(path):  # 判断是否为文件夹
        for root, dirs, files in os.walk(path):
            files = natsorted(files)
            for file in files:
                split = os.path.splitext(file)
                if split[1] == '.flv':
                    file_list.append(path + os.sep + split[0])
    elif os.path.isfile(path):
        file_list.append(os.path.splitext(path)[0])
    sys.stdout.write(f' OK, {len(file_list)} files found\n')
    sys.stdout.flush()

    sys.stdout.write('Converting...\n')
    sys.stdout.flush()

    # 开始转换
    def Run():
        result_list = []

        def get_seconds(process_time):
            if process_time is None:
                return 0

            h = int(process_time[0:2])
            # print("时：" + str(h))
            m = int(process_time[3:5])
            # print("分：" + str(m))
            s = int(process_time[6:8])
            # print("秒：" + str(s))
            ms = int(process_time[9:12])
            # print("毫秒：" + str(ms))
            ts = (h * 60 * 60) + (m * 60) + s + (ms / 1000)
            return ts

        # ffmpeg任务
        async def ffmpeg_task(filename):
            cmd = f'{ffmpeg_path} -i "{filename}.flv" ' \
                  f'-y -vcodec copy -acodec copy ' \
                  f'"{filename}.mp4"'
            process = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       encoding="utf-8",
                                       text=True)

            lsat_progress = 0
            is_init = False

            widgets = [
                progressbar.Percentage(),
                ' ', progressbar.Bar(), ' ',
                progressbar.Timer()
            ]
            bar = progressbar.ProgressBar(max_value=100, widgets=widgets)
            for line in process.stdout:
                if not is_init:
                    sys.stderr.write('\n' + os.path.basename(filename) + ':\n')
                    sys.stdout.flush()
                    bar.update(0)
                    is_init = True

                duration_res = re.search(r'\sDuration: (?P<duration>\S+)', line)
                if duration_res is not None:
                    duration = duration_res.groupdict()['duration']
                    duration = re.sub(r',', '', duration)

                result = re.search(r'\stime=(?P<time>\S+)', line)
                if result is not None:
                    elapsed_time = result.groupdict()['time']
                    progress = (get_seconds(elapsed_time) / get_seconds(duration)) * 100
                    if progress >= 100:
                        progress = 100
                    progress = round(progress, 1)
                    if lsat_progress < progress <= 100:
                        bar.update(progress)
                        progressbar.streams.flush()
                        lsat_progress = progress

            process.wait()

            if process.poll() == 0:
                # sys.stdout.write(f'\nThe conversion of "{filename}.flv" is finished\n')
                # sys.stdout.flush()
                result_list.append(filename)
            else:
                sys.stderr.write(f'\nThe conversion of "{filename}.flv" is failed\n')
                sys.stderr.flush()

            process.kill()

        loop.run_until_complete(asyncio.wait([ffmpeg_task(flv_file) for flv_file in file_list]))

        sys.stdout.write(f'\nOK, {len(result_list)} files convert successfully, total {len(file_list)} files\n')
        sys.stdout.flush()
        sys.stdout.write('Process finished\n')
        sys.stdout.flush()

    Run()


if __name__ == '__main__':
    start = time.perf_counter()
    sys.stdout.write('Enter the path of target file or directory: ')
    sys.stdout.flush()
    flv_to_mp4(sys.stdin.readline()[:-1])
    sys.stdin.flush()
    end = time.perf_counter()
    sys.stdout.write('\nRunning time: %s Seconds' % (end - start))
    sys.stdout.flush()
