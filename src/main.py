import argparse
import json
import os
from tkinter import *

from logger import configure_logger
from trainBoard import StationBoard


def loadConfig():
    # Look for config.json in current working directory
    config_path = "config.json"

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"config.json not found in current directory: {os.getcwd()}"
        )

    with open(config_path, "r") as programConfig:
        config = json.load(programConfig)
        return config


if __name__ == "__main__":
    # Configure logger at application startup
    logger = configure_logger()
    logger.info("Starting trainBoard application")

    config = loadConfig()
    station = config["stationCode"]
    logger.info(f"Loaded configuration for station: {station}")

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", action="store_true")
    args = parser.parse_args()

    StationBoard(station, config["api_token"], test=args.test)
