"""This file is for execution from the command line via 'python cyckei.py'."""
from cyckei import cyckei
import sys
import os

if __name__ == '__main__':
    try:
        cyckei.main()
    except KeyboardInterrupt as error:
        print(f"Got keyboard interrupt: {error}")
        try:
            sys.exit(0)
        except SystemExit as error:
            print(f"sys.exit failed: {error}")
            os._exit(0)
