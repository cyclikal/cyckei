import zmq

import functions as func
from server import server


def main(record_dir="Cyckei"):
    """
    Begins execution of Cyckei.

    Args:
        record_dir: Optional path to recording directory.
    Returns:
        Result of app.exec_(), Qt's main event loop.

    """
    try:
        config, record_dir = func.configuration.read_config(record_dir)
        logger = func.configuration.setup_logging('cyckei', record_dir, config)

    except Exception as e:
        print("An error occured before logging began.")
        print(e)

    logger.info(
        f"cyckei_server.main: Initializing Cyckei Server version {config['version']}")
    logger.debug("cyckei.main: Logging at debug level")

    # Create Server's ZMQ Socket
    logger.debug("cyckei.server.server.main: Binding socket")
    try:
        context = zmq.Context(1)
        socket = context.socket(zmq.REP)
        socket.bind("{}:{}".format(config["zmq"]["server-address"],
                                   config["zmq"]["port"]))

    except zmq.error.ZMQError as error:
        logger.critical(f"It appears the server is already running: {error}")
        msg = [
            "Cyckei Instance Already Running!",
            "To show client, open taskbar widget and click \"Launch Client\"",
            "Failed to initialize socket. "
            "This indicates an existing server insance. "
            f"Error: {error}"]
        print('\n'.join(msg))
        return
        
    logger.debug("cyckei.server.server.main: Socket bound successfully")

    # Start Server
    logger.debug("cyckei.main: Starting Server")

    server.main(config, socket)


if __name__ == "__main__":
    print("Starting Cyckei Server...")
    main()
