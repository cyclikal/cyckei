from subprocess import Popen, DEVNULL
from pkg_resources import require, DistributionNotFound


def main():

    try:
        version = require("cyckei")[0].version
    except DistributionNotFound:
        version = "(unpackaged)"

    print("\nWelcome to Cyckei {}!".format(version))
    Popen(["cyckei-client"], stdout=DEVNULL)
    Popen(["cyckei-server"], stdout=DEVNULL)


if __name__ == "__main__":
    main()
