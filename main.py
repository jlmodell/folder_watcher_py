import json
import logging
import os
import re
import sys
import time

import redis
import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

LOG_PATH = os.path.join(r"//busse/home", "folder_watcher.log")
if not os.path.exists(LOG_PATH):
    LOG_PATH = os.path.join(os.getcwd(), "folder_watcher.log")

CONFIG_PATH = os.path.join(r"C:\temp", "global", "config.yaml")
if not os.path.exists(CONFIG_PATH):
    CONFIG_PATH = os.path.join(os.getcwd(), "config.yaml")
    assert os.path.exists(CONFIG_PATH), "Config file not found"

NEW_FILES_QUEUE = "queue:new_files"

# ------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# ------------------------------------------------------------

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)


def setup_redis(redis_config: dict[str, str] = None):
    print(redis_config)
    if not redis_config:
        logger.error("Redis config not found")
    if [key for key in redis_config.keys() if key not in ["url", "pass"]]:
        logger.error("Redis config contains invalid keys")
        raise ValueError("Redis config contains invalid keys")

    url, port = redis_config["url"].split(":")
    password = redis_config["pass"]

    return redis.Redis(host=url, port=int(port), password=password, db=0)


rdb = setup_redis(config["redis"])

# ------------------------------------------------------------


class FolderUpdateHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_processed = None
        self.debounce_time = 1.0

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        file_name = os.path.basename(file_path)

        if os.path.splitext(file_name)[
            1
        ].lower() == ".xls" and file_name.upper().startswith("E"):
            now = time.time()

            if self.last_processed and now - self.last_processed < self.debounce_time:
                return

            self.last_processed = now

            logger.info(f"Updated file detected: {file_name}")

            year_regex = re.compile(r"\\(\d{4})\s")
            year = year_regex.search(file_path).group(1)

            send_to_queue(year, file_name)


def send_to_queue(year: str, file_name: str):
    object = json.dumps(
        {
            "year": year,
            "file_name": file_name,
        }
    )

    logger.info("Sending to queue: %s", object)

    rdb.rpush(NEW_FILES_QUEUE, object)


def monitor_folder(folder_path):
    event_handler = FolderUpdateHandler()
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()

    logger.debug(f"Monitoring updates in folder: {folder_path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


# ------------------------------------------------------------


def main(path=None):
    if path is None or path == "":
        path = input("Enter path: ")
    logger.debug("path: %s", path)

    if not os.path.exists(path):
        logger.error("Path not found: %s", path)
        raise ValueError("Path not found: %s" % path)

    monitor_folder(path)


if __name__ == "__main__":
    args = sys.argv[1:]
    network_path = " ".join(args)

    main(path=network_path)
