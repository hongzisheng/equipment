import os

import whisper

from app.utils.extract_text_from_file import handle_video

# === 配置 ===
RTMP_URL = ''  # 你的 OBS 推流地址
RECORD_DIR = ''
TRANSCRIPT_DIR = ''
SEGMENT_DURATION = 10  # 每段 10 秒

# 加载 Whisper 模型（一次加载，多次使用）
print("Loading Whisper model...")
model = whisper.load_model("small")  # 可选: tiny, base, small, medium, large
print("Whisper model loaded.")


def init_dirs(current_app):
    global RECORD_DIR, TRANSCRIPT_DIR,RTMP_URL
    RTMP_URL = current_app.config.get('RTMP_URL')
    RECORD_DIR = current_app.config.get('RECORD_DIR')
    TRANSCRIPT_DIR = current_app.config.get('TRANSCRIPT_DIR')

def transcribe_audio(video_path: str) -> str:
    """从视频中提取音频并转文字"""
    try:
        # 修改为只接收一个返回值，忽略第二个返回值
        segments = model.transcribe(video_path, language="zh", beam_size=5)
        # 如果返回的是字典形式的结果，提取segments
        if isinstance(segments, dict):
            segments = segments['segments']
        text = "".join([seg.text for seg in segments])
        return text.strip()
    except Exception as e:
        print(f"ASR error: {e}")
        return "[语音识别失败]"


def status():
    video_count = len([f for f in os.listdir(RECORD_DIR) if f.endswith(".mp4")])
    txt_count = len([f for f in os.listdir(TRANSCRIPT_DIR) if f.endswith(".txt")])
    return {
        "status": "running",
        "recordings": video_count,
        "transcripts": txt_count,
        "rtmp_url": RTMP_URL
    }


def latest():
    """返回最新字幕"""
    txt_files = sorted(
        [f for f in os.listdir(TRANSCRIPT_DIR) if f.endswith(".txt")],
        key=lambda x: os.path.getmtime(os.path.join(TRANSCRIPT_DIR, x)),
        reverse=True
    )
    if not txt_files:
        return {"text": "", "file": ""}

    latest_file = txt_files[0]
    with open(os.path.join(TRANSCRIPT_DIR, latest_file), "r", encoding="utf-8") as f:
        text = f.read()
    return {"text": text, "file": latest_file}


import threading
import time
import os
import subprocess
from datetime import datetime

# 添加全局变量控制录制状态
recording_thread = None
recording_stop_event = threading.Event()


def record_and_transcribe():
    """后台任务：循环录制 + 转文字"""
    while not recording_stop_event.is_set():  # 检查停止事件
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_file = os.path.join(RECORD_DIR, f"clip_{timestamp}.mp4")

            # 使用 FFmpeg 录制 10 秒视频（从 RTMP 流）
            cmd = [
                "ffmpeg",
                "-i", RTMP_URL,
                "-t", str(SEGMENT_DURATION),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-y",  # 覆盖
                video_file
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"保存完成 {video_file} 当前时间：", datetime.now())

            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr.decode()}")
                time.sleep(1)
                continue

            # 语音识别
            print(f"开始处理：Transcribing {video_file}...当前时间：", datetime.now())
            transcript = handle_video(video_file)

            # 保存文字
            txt_file = os.path.join(TRANSCRIPT_DIR, f"clip_{timestamp}.txt")
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write(transcript)

            print(f"✅ Saved: {video_file} | Text: {transcript[:50]}...")

        except Exception as e:
            print(f"Record loop error: {e}")
            time.sleep(2)

        # 精确控制间隔（避免累积误差）
        time.sleep(0.1)


def start_recording():
    """启动录制和转录"""
    global recording_thread, recording_stop_event

    # 如果已经在录制，则不重复启动
    if recording_thread is not None and recording_thread.is_alive():
        print("Recording is already running!")
        return False

    # 清除停止事件并启动新线程
    recording_stop_event.clear()
    recording_thread = threading.Thread(target=record_and_transcribe)
    recording_thread.daemon = True
    recording_thread.start()
    print("流式数据处理开始！当前时间：", datetime.now())
    return True


def stop_recording():
    """停止录制和转录"""
    global recording_thread

    if recording_thread is None or not recording_thread.is_alive():
        print("Recording is not running!")
        return False

    # 设置停止事件，等待线程结束
    recording_stop_event.set()
    recording_thread.join(timeout=5)  # 等待最多5秒
    print("Recording stopped!")
    return True


def is_recording():
    """检查当前是否正在录制"""
    return recording_thread is not None and recording_thread.is_alive()

