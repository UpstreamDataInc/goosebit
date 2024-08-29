import argparse
from pathlib import Path

parser = argparse.ArgumentParser(prog="gooseBit")
parser.add_argument("settings_file", default=None, type=Path, nargs="?")
