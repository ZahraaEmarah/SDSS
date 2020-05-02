import sys
import os
import threading
import socket
import time
import datetime
import uuid
import struct

# https://bluesock.org/~willkg/dev/ansi.html
ANSI_RESET = "\u001B[0m"
ANSI_RED = "\u001B[31m"
ANSI_GREEN = "\u001B[32m"
ANSI_YELLOW = "\u001B[33m"
ANSI_BLUE = "\u001B[34m"

_NODE_UUID = str(uuid.uuid4())[:8]


def print_yellow(msg):
    print(f"{ANSI_YELLOW}{msg}{ANSI_RESET}")


def print_blue(msg):
    print(f"{ANSI_BLUE}{msg}{ANSI_RESET}")


def print_red(msg):
    print(f"{ANSI_RED}{msg}{ANSI_RESET}")


def print_green(msg):
    print(f"{ANSI_GREEN}{msg}{ANSI_RESET}")


def get_broadcast_port():
    return 35498


def get_tcp_port():  # return the tcp port number
    return str(server.getsockname()[1])


def get_node_uuid():
    return _NODE_UUID


class NeighborInfo(object):
    def __init__(self, delay, last_timestamp, ip=None, tcp_port=None):
        # Ip and port are optional, if you want to store them.
        self.delay = delay
        self.last_timestamp = last_timestamp
        self.ip = ip
        self.tcp_port = tcp_port


############################################
#######  Y  O  U  R     C  O  D  E  ########
############################################


# Don't change any variable's name.
# Use this hashmap to store the information of your neighbor nodes.
neighbor_information = {}
# Leave the server socket as global variable.
# TCP
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 0))  # set a random port number

# Leave broadcaster as a global variable.
# UDP
broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Setup the UDP socket

broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
if broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) == -1:
    print_red("setsockopt (SO_BROADCAST)")  # if error
    exit(1)
broadcaster.bind(('', get_broadcast_port()))


def send_broadcast_thread():
    node_uuid = get_node_uuid()
    tcp_port = get_tcp_port()
    # print that you are available
    print_green(f"[UDP] Device -> EVERYBODY : {node_uuid} ON {tcp_port} ")
    message = node_uuid + " ON " + tcp_port
    counter = 0
    while True:
        # TODO: write logic for sending broadcasts.
        broadcaster.sendto(message.encode('UTF-8'), ('255.255.255.255', get_broadcast_port()))
        counter = counter + 1
        time.sleep(1)  # Leave as is.


def receive_broadcast_thread():
    """
    Receive broadcasts from other nodes,
    launches a thread to connect to new nodes
    and exchange timestamps.
    """
    uuids = []
    while True:
        # TODO: write logic for receiving broadcasts.
        data, (ip, port) = broadcaster.recvfrom(4096)
        print_blue(f"RECV: {data} FROM: {ip}:{port}")
        # start parsing
        msg = data.decode("utf-8")
        msg_array = msg.split()
        other_uuid = msg_array[0]
        tcp_port = msg_array[2]

        args = (other_uuid, ip, int(tcp_port))
        print_red(args)
        # send timestamp
        if other_uuid not in uuids:
            thread3 = daemon_thread_builder(exchange_timestamps_thread, args)
            thread3.start()
            thread3.join()
        uuids.append(other_uuid)


def tcp_server_thread():
    """
    Accept connections from other nodes and send them
    this node's timestamp once they connect.
    """
    thread1 = daemon_thread_builder(send_broadcast_thread)
    thread2 = daemon_thread_builder(receive_broadcast_thread)
    thread1.start()
    thread2.start()
    while True:
        server.listen(50)
        print_red("waiting for client")
        c_socket, address = server.accept()
        data = c_socket.recv(1024)
        print_green(f"Client accepted is {c_socket.getsockname()[1]} the message is {data}")
        received_stamp = struct.unpack("d", data)
        print(f"received timestamp {received_stamp}")
        now = datetime.datetime.utcnow().timestamp()
        delay = now - received_stamp[0]
        print_red(f"DEELLAAYYYY ISS {delay}")

    pass


def exchange_timestamps_thread(other_uuid: str, other_ip: str, other_tcp_port: int):
    """
    Open a connection to the other_ip, other_tcp_port
    and do the steps to exchange timestamps.
    Then update the neighbor_info map using other node's UUID.
    """
    # if other_uuid = my_uuid don't connect
    if other_uuid == get_node_uuid():
        return

    print_yellow(f"ATTEMPTING TO CONNECT TO {other_uuid}")
    timestamp = datetime.datetime.utcnow().timestamp()
    print(f"sent timestamp {timestamp}")
    timestamp = bytearray(struct.pack("d", timestamp))

    # send time stamp to the source of the message
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((other_ip, other_tcp_port))

    try:
        client_socket.sendall(timestamp)
        time.sleep(1)
    except socket.error as e:
        print_red("ERROR")
    except IOError as e:
        print_red("error pipe")

    client_socket.close()
    pass


def daemon_thread_builder(target, args=()) -> threading.Thread:
    """
    Use this function to make threads. Leave as is.
    """
    th = threading.Thread(target=target, args=args)
    th.setDaemon(True)
    return th


def entrypoint():
    #thread1 = daemon_thread_builder(send_broadcast_thread)
    #thread2 = daemon_thread_builder(receive_broadcast_thread)
    thread3 = daemon_thread_builder(tcp_server_thread())
    #thread1.start()
    #thread2.start()
    thread3.start()
    #thread1.join()
    #thread2.join()
    thread3.join()
    pass


############################################
############################################


def main():
    """
    Leave as is.
    """
    print("*" * 50)
    print_red("To terminate this program use: CTRL+C")
    print_red("If the program blocks/throws, you have to terminate it manually.")
    print_green(f"NODE UUID: {get_node_uuid()}")
    print("*" * 50)
    time.sleep(2)  # Wait a little bit.
    entrypoint()


if __name__ == "__main__":
    main()