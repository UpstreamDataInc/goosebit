#!/usr/bin/env python3

from time import sleep


def main() -> None:
    while True:
        print("Hello!", flush=True)
        sleep(5)


if __name__ == "__main__":
    main()
