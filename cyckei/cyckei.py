from subprocess import Popen, run
from pkg_resources import require, DistributionNotFound


def main():

    try:
        version = require("cyckei")[0].version
    except DistributionNotFound:
        version = "(unpackaged)"

    print("\nWelcome to Cyckei {}!".format(version))
    print("Starting client...")
    Popen(["cyckei-client"])
    run(["cyckei-server"])


if __name__ == "cyckei":
    main()
