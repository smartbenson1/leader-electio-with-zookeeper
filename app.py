from flask import Flask
import os
import logging
from kazoo.client import KazooClient
import threading
import socket
import time
import signal
# import random

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

is_leader = False
zk = None
my_node = None
leader_path = '/api-leader'

def leader_election():
    global is_leader, zk, my_node
    zk_host = os.getenv('ZK_HOST', 'zookeeper-headless')
    zk_port = int(os.getenv('ZK_PORT', 2181))

    try:
        with socket.create_connection((zk_host, zk_port), timeout=5):
            logging.info(f'Connected to ZooKeeper at {zk_host}:{zk_port}')
    except socket.error as e:
        logging.error(f"Error: Unable to connect to {zk_host}:{zk_port} - {e}")
        return

    zk = KazooClient(hosts=f'{zk_host}:{zk_port}')
    zk.start()

    # Ensure the parent node exists
    zk.ensure_path(leader_path)

    my_node = None

    def watch_children(event):
        # This function is called when there's a change in the leader_path
        check_leadership()

    def check_leadership():
        global is_leader
        children = zk.get_children(leader_path)
        children.sort()
        if my_node and my_node.split('/')[-1] == children[0]:
            if not is_leader:
                logging.info("This instance is now the leader")
                is_leader = True
        else:
            if is_leader:
                logging.info("This instance is no longer the leader")
            is_leader = False

    while True:
        try:
            if not my_node or not zk.exists(my_node):
                my_node = zk.create(f"{leader_path}/node-", b"", ephemeral=True, sequence=True)
                logging.info(f"Created node: {my_node}")

            # Set the watch and immediately check leadership
            zk.get_children(leader_path, watch=watch_children)
            check_leadership()

            if is_leader:
                break
            else:
                logging.info("Waiting to become leader")
                time.sleep(5)  # Wait before checking again
        except Exception as e:
            logging.error(f"Error in leader election: {e}", exc_info=True)
            time.sleep(5)

    logging.info("Exiting leader election loop")

@app.route('/')
def hello():
    if is_leader:
        return 'hello from leader', 200
    else:
        return 'hello from follower', 200

def handle_shutdown(sig, frame):
    global is_leader, zk, my_node
    if zk:
        try:
            if my_node and zk.exists(my_node):
                zk.delete(my_node)
                logging.info(f"Deleted node: {my_node}")
        except Exception as e:
            logging.error(f"Failed to clean up ZooKeeper node: {e}")
        finally:
            zk.stop()
            zk.close()

    logging.info("Shutting down gracefully...")
    exit(0)

if __name__ == '__main__':
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Start the leader election in a separate thread
    threading.Thread(target=leader_election, daemon=True).start()

    while True:
        if is_leader:
            logging.info("Starting Flask app as leader")
            app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
            break
        else:
            logging.info("Waiting to become leader")
            time.sleep(1)  # Sleep briefly before checking again