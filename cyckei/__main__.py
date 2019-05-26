import sys
import pkg_resources


def main(args=None):
    """
        This is the main entrypoint and routine of Cyckei Vayu.
        Vayu aims to make cyckei more efficient in many aspects.
        This primarily includes distribution and client-server communication.
    """
    if args is None:
        args = sys.argv[1:]

    version = pkg_resources.require("cyckei")[0].version

    print("Welcome to Cyckei Vayu version {}".format(version))

    # Do argument parsing here (eg. with argparse) and anything else.


if __name__ == "__main__":
    main()
