import sys
import pandas as pd
from pathlib import Path
import time
import threading


def setup_notebook():
    project_root = Path.cwd().parent
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    from src.utils.styling import StyleManager

    return StyleManager()


def loading_animation(stop):
    i = 0
    while not stop.is_set():
        print(f"\rLoading files{'.' * (i % 4):<3}", end="", flush=True)
        time.sleep(0.3)
        i += 1


def load_files(paths: list):
    stop_flag = threading.Event()
    loading_thread = threading.Thread(
        target=loading_animation, args=(stop_flag,)
    )
    loading_thread.start()

    try:
        data_frames = [pd.read_parquet(path) for path in paths]
    finally:
        stop_flag.set()
        loading_thread.join()
        print("\rFiles loaded successfully.")

    return tuple(data_frames)
