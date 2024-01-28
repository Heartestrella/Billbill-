"""
Making by heartbeat Github: https://github.com/Heartestrella/Billbill-
Version : V1.0.1
"""
import os
import time
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread, Event, Lock
import requests
from flask import Flask, jsonify, request
from flask_socketio import SocketIO


decoder = json.JSONDecoder()
app = Flask(__name__)
socketio = SocketIO(app)
app.logger = None
import logging

log = logging.getLogger("werkzeug")
log.disabled = True
socketio = SocketIO(app, async_mode="threading")


def check_and_create_playing_file():
    file_name = "playing.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)


# 原文链接：https://egg.moe/2020/07/get-netease-cloudmusic-playing 感激不尽
class LoggingEventHandler(FileSystemEventHandler):
    def __init__(self):
        self.file_size = 0
        self.timing = 2  # About tow seconds delay
        self.stop_timing_thread = Event()
        self.start_timing_thread = None
        self.lyric = None
        self.music_name = None
        self.artist_list = None
        self.duration = None
        self.data = {
            "AppName": "网易云音乐",  # Only for
            "Title": "",  # Music name and artist
            "AllTime": "",  # 总时长
            "Now": "",  # 当前播放时长
            "ChineseLryic": "",  # 中文翻译
            "Lryic": "",  # 歌词
            "FormattedTime": "",  # 当前播放/总时长
        }
        self.return_data = None

    # 原文链接：https://blog.csdn.net/weixin_45576923/article/details/113815385 十分感激
    def get_lyric(self, song_id):
        try:
            headers = {
                "user-agent": "Mozilla/5.0",
                "Referer": "http://music.163.com",
                "Host": "music.163.com",
            }
            if not isinstance(song_id, str):
                song_id = str(song_id)
            url = f"http://music.163.com/api/song/lyric?id={song_id}+&lv=1&tv=-1"

            r = requests.get(url, headers=headers)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            json_obj = json.loads(r.text)

            lyric_data = {
                "lrc": json_obj["lrc"]["lyric"],
                "tlyric": json_obj["tlyric"]["lyric"] if "tlyric" in json_obj else None,
            }

            return lyric_data
        except:
            time.sleep(3)
            self.get_lyric(song_id)

    def get_history_file(self):
        path = os.path.join(
            os.path.expanduser("~"), r"AppData\Local\Netease\CloudMusic\webdata\file"
        )
        if os.path.exists(path):
            return path
        else:
            print("cloudmusic data folder not found")
            exit(1)

    def start_timing(self, lyric: list):
        if lyric:
            lrcDict = {}
            lrcDict_cn = {}
            lyric, cnlrc = lyric[0], lyric[1]
            musicList = lyric.splitlines()
            if cnlrc:
                index_of_first_newline = cnlrc.find("\n")
                cnlrc = cnlrc[index_of_first_newline + 1 :]
                cnlrclist = cnlrc.splitlines()
                print(cnlrclist)
                for lrcLine in cnlrclist:
                    lrcLineList = lrcLine.split("]")
                    for index in range(len(lrcLineList) - 1):
                        timeStr = lrcLineList[index][1:]
                        timeList = timeStr.split(":")
                        timea = float(timeList[0]) * 60 + float(timeList[1])
                        lrcDict_cn[timea] = lrcLineList[-1]
                allTimeList_cn = []
                for t in lrcDict_cn:
                    allTimeList_cn.append(t)
            allTimeList = []

            for lrcLine in musicList:
                lrcLineList = lrcLine.split("]")
                for index in range(len(lrcLineList) - 1):
                    timeStr = lrcLineList[index][1:]
                    timeList = timeStr.split(":")
                    timea = float(timeList[0]) * 60 + float(timeList[1])
                    lrcDict[timea] = lrcLineList[-1]

            for t in lrcDict:
                allTimeList.append(t)
            allTimeList.sort()

            getTime = self.timing
            while not self.stop_timing_thread.is_set():
                self.timing += 1
                for n in range(len(allTimeList)):
                    tempTime = allTimeList[n]
                    if getTime < tempTime:
                        break
                lrc = lrcDict.get(allTimeList[n])
                if cnlrc:
                    for n in range(len(allTimeList_cn)):
                        tempTime = allTimeList_cn[n]
                        if getTime < tempTime:
                            break
                    lrc_cn = lrcDict_cn.get(allTimeList_cn[n])
                if not lrc and not lrc:
                    pass
                else:
                    # print(lrc)
                    data = self.data
                    all_time = int(int(self.duration) / 1000)
                    data["Title"] = f"{self.music_name} by {self.artist_list}"
                    data["AllTime"] = all_time
                    data["Now"] = self.timing
                    data["Lryic"] = lrc
                    if cnlrc:
                        data["ChineseLryic"] = lrc_cn
                    data["FormattedTime"] = self.format_time(self.timing, all_time)
                    self.return_data = data
                    with open("playing.json", mode="w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(data)
                if n in range(len(allTimeList) - 1):
                    time.sleep(allTimeList[n + 1] - allTimeList[n])
                    getTime += allTimeList[n + 1] - allTimeList[n]
                else:
                    break

    def get_bgm_info(self):
        data = self.return_data
        print(self.return_data)
        if data:
            return data

    def format_time(self, current_time, total_time):
        current_minutes, current_seconds = divmod(current_time, 60)
        total_minutes, total_seconds = divmod(total_time, 60)

        formatted_time = f"({int(current_minutes)}:{int(current_seconds)}/{int(total_minutes)}:{int(total_seconds)})"
        return formatted_time

    def on_modified(self, event):
        super(LoggingEventHandler, self).on_modified(event)
        path = event.src_path

        if path.endswith(r"webdata\file\history"):
            current_size = os.path.getsize(path)
            if current_size != self.file_size:
                self.file_size = current_size
                for _ in range(5):
                    try:
                        song, artists, song_of_id = self.get_playing(path)
                        lyric = self.get_lyric(song_of_id)
                        lrc, cnlrc = lyric["lrc"], lyric["tlyric"]
                        playing = f'{song} - {" / ".join(artists)}'
                        #  print(playing)
                        if playing:
                            if self.start_timing_thread:
                                self.stop_timing_thread.set()
                                self.start_timing_thread.join()
                            self.timing = 2  # 识别到歌曲后开启计时
                            self.stop_timing_thread.clear()
                            self.start_timing_thread = Thread(
                                target=self.start_timing, args=([lrc, cnlrc],)
                            )
                            self.start_timing_thread.start()

                        break
                    except PermissionError:
                        time.sleep(1)

    def get_playing(self, path):
        track_info = dict()
        with open(path, encoding="utf-8") as f:
            while True:
                try:
                    read_string = f.read(3200)
                    read_string += f.read(500)
                    decoded_json = decoder.raw_decode(read_string[1:])
                    track_info.update(decoded_json[0])
                    break
                except json.JSONDecodeError:
                    time.sleep(0.1)

        if not track_info:
            return None

        track_name = track_info["track"]["name"]
        artist_list = [i["name"] for i in track_info["track"]["artists"]]
        id_of_song = track_info["track"]["id"]
        duration = track_info["track"]["duration"]

        self.music_name = track_name
        self.artist_list = artist_list
        self.duration = duration
        return track_name, artist_list, id_of_song

    def main(self):
        path = self.get_history_file()
        event_handler = LoggingEventHandler()
        observer = Observer()
        observer.schedule(event_handler, path, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            observer.stop()
        observer.join()


if __name__ == "__main__":
    check_and_create_playing_file()
    log = LoggingEventHandler()

    @app.route("/BGMName/")
    def get_bgm_info():
        with open("playing.json", "r", encoding="utf-8") as json_file:
            data_read = json.load(json_file)
        if data_read:
            return jsonify(data_read)
        else:
            return jsonify({})

    socketio = SocketIO(app, logger=log)
    socketio.start_background_task(log.main)
    socketio.run(app, debug=True, port=62333)
