import json
import logging
import os
import re
import sys
import time

import redis
import yaml

# from watchdog.events import FileSystemEventHandler
# from watchdog.observers import Observer

LOG_PATH = os.path.join(r"//busse/home", "folder_watcher.log")
if not os.path.exists(LOG_PATH):
    LOG_PATH = os.path.join(os.getcwd(), "folder_watcher.log")

CONFIG_PATH = os.path.join(r"C:\temp", "global", "config.yaml")
if not os.path.exists(CONFIG_PATH):
    CONFIG_PATH = os.path.join("/app", "config.yaml")
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


def setup_redis(redis_config=None):
    if redis_config is None:
        logger.error("Redis config not found")

    if isinstance(redis_config, dict):
        if "url" not in redis_config or "pass" not in redis_config:
            logger.error("Redis config contains invalid keys")
            raise ValueError("Redis config contains invalid keys")

    url, port = redis_config["url"].split(":")
    password = redis_config["pass"]

    return redis.Redis(host=url, port=int(port), password=password, db=0)


rdb = setup_redis(config["redis"])

# ------------------------------------------------------------


def monitor_folder(dir_path: str):
    """Watch a folder for new files and send them to a queue."""

    last_processed = None
    year_regex = re.compile(r"\\(\d{4})\s")

    while True:
        # Get a list of all files in the directory
        files = os.listdir(dir_path)

        # Filter the list to only include .xls files starting with "E"
        xls_files = [
            file
            for file in files
            if file.lower().endswith(".xls") and file.upper().startswith("E")
        ]

        # Sort the list of .xls files by modification time
        xls_files.sort(key=lambda file: os.path.getmtime(os.path.join(dir_path, file)))

        # Iterate over the list of .xls files and send new files to the queue
        for file in xls_files:
            # Check if the file has already been processed
            if (
                last_processed is not None
                and os.path.getmtime(os.path.join(dir_path, file)) <= last_processed
            ):
                continue

            # Extract the year from the file name
            year_match = year_regex.search(file)
            if year_match is None:
                continue
            year = year_match.group(1)

            # Send the file to the queue
            object = json.dumps(
                {
                    "year": year,
                    "file_name": file,
                }
            )

            logger.debug("Sending to queue: %s", object)

            rdb.rpush(NEW_FILES_QUEUE, object)

        # Update the last_processed time
        if xls_files:
            last_processed = os.path.getmtime(os.path.join(dir_path, xls_files[-1]))

        # Wait for 5 seconds before checking the directory again
        time.sleep(5)


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
