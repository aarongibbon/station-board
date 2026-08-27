import argparse
import json
import os
from tkinter import *

from _version import __version__
from logger import configure_logger
from stationBoard import StationBoard


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


def getScreenDimensions():
    root = Tk()
    root.withdraw()
    dimensions = (root.winfo_screenwidth(), root.winfo_screenheight())
    root.destroy()
    return dimensions


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", action="store_true")
    parser.add_argument("--version", action="version", version=f"{__version__}")
    args = parser.parse_args()

    # Configure logger at application startup
    logger = configure_logger()
    logger.info("Starting station-board application")

    config = loadConfig()
    station = config["stationCode"]
    logger.info(f"Loaded configuration for station: {station}")
    platform_board_width = config.get("platform_board_width")
    platform_board_height = config.get("platform_board_height")
    if platform_board_width is None or platform_board_height is None:
        screen_width, screen_height = getScreenDimensions()
        platform_board_width = platform_board_width or screen_width
        platform_board_height = platform_board_height or screen_height

    StationBoard(
        station,
        config["api_token"],
        platform_board_width=platform_board_width,
        platform_board_height=platform_board_height,
        test=args.test,
    )
