import argparse
import json
import os
from tkinter import *

from _version import __version__
from logger import configure_logger
from stationBoard import StationBoard

DEFAULT_PLATFORMS = [1, 2]


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


def validate_positive_dimension(name, value):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}")


def validate_platforms(platforms):
    if not isinstance(platforms, list) or not platforms:
        raise ValueError("platforms must be a non-empty list")
    if any(
        isinstance(platform, bool) or not isinstance(platform, int) or platform <= 0
        for platform in platforms
    ):
        raise ValueError("platforms must contain only positive integers")
    if len(platforms) != len(set(platforms)):
        raise ValueError("platforms must not contain duplicates")


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
    logger.info(f"Loaded configuration from config.json for station: {station}")
    logger.debug(f"Configuration keys loaded: {sorted(config.keys())}")
    platforms = config.get("platforms", DEFAULT_PLATFORMS)
    validate_platforms(platforms)
    logger.info(f"Configured platforms: {platforms}")

    station_board_width = config.get("station_board_width")
    station_board_height = config.get("station_board_height")
    logger.debug(
        f"Configured station dimensions: width={station_board_width}, "
        f"height={station_board_height}"
    )
    if station_board_width is None or station_board_height is None:
        logger.info("Station dimensions not fully configured; detecting display size")
        screen_width, screen_height = getScreenDimensions()
        logger.info(f"Detected display dimensions: {screen_width}x{screen_height}")
        if station_board_width is None:
            station_board_width = screen_width
        if station_board_height is None:
            station_board_height = screen_height
        logger.info(
            f"Using resolved station dimensions: "
            f"{station_board_width}x{station_board_height}"
        )
    else:
        logger.info("Using station dimensions from configuration")

    validate_positive_dimension("station_board_width", station_board_width)
    validate_positive_dimension("station_board_height", station_board_height)
    platform_board_width = station_board_width
    platform_board_height = station_board_height // len(platforms)
    logger.info(
        f"Starting station board with dimensions: "
        f"{station_board_width}x{station_board_height}; "
        f"platform height: {platform_board_height}"
    )

    StationBoard(
        station,
        config["api_token"],
        platforms=platforms,
        platform_board_width=platform_board_width,
        platform_board_height=platform_board_height,
        test=args.test,
    )
