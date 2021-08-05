#!/bin/python

import os
import sys

# add parent directory to path
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from builder import Builder, load_builder, save_builder


def main():
    builder = load_builder()
    builder.download_ninja()
    save_builder(builder)


if __name__ == "__main__":
    main()
