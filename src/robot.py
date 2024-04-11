import socket
from time import sleep
from dataclasses import dataclass
from enum import Enum
from struct import pack, unpack

DEFAULT_PORT = 44818
DEFAULT_IP = 'localhost'

class TaskId(Enum):
    IDLE: int = 0
    MOVE: int = 1
    COLLECT: int = 2
    RETURN: int = 3
    DONE: int = 4
    ERROR: int = 5
    INIT: int = 6

@dataclass
class Vec3:
    x: float
    y: float
    z: float

@dataclass
class Task:
    task: TaskId
    loc: Vec3

class Robot:
    def __init__(self, ip=DEFAULT_IP, port=DEFAULT_PORT):
        # initial socket creation
        self.id = -1
        self.loc = Vec3(0, 0, 0)
        self.task = Task(TaskId.INIT, self.loc)
        self.address = (ip, DEFAULT_PORT)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.address)
        print("[INFO] CONNECTION TO SERVER ESTABLISHED")
        con = self.get_id()
        self.encode = self.id.to_bytes(1, "little")
        # connection failure loop
        if con == 1:
            for x in range(0,2):
                if con == 0: break
                # reconnect socket
                self.sock.close()
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect(self.address)
                con = self.get_id()
                if x == 2 and con != 0:
                    # absolute connection failure
                    print("[ERROR] COULD NOT CONNECT: CHECK SERVER STATUS, IP, AND PORT")
                    exit()
        if self.id > -1: print("[INFO] ROBOT ASSIGNED ID(", self.id, ")")
        else: print("[ERROR] ROBOT NOT ASSIGNED ID")

    def run(self):
        self.update()
        while True:
            task = self.get_task()
            self.exec_task(task)

    def get_id(self) -> int:
        self.sock.send(b'reb')
        msg = self.sock.recv(1024)
        if (msg[0:2] == b'r@'):
            self.id = msg[2]
            return 0
        else:
            print("[WARN] CONNECTION FAILED")
            return 1

    def serialize_loc(self) -> bytes:
        return pack('fff', self.loc.x, self.loc.y, self.loc.z)

    def deserialize_loc(self, data: bytes) -> Vec3:
        loc = unpack('fff', data)
        return Vec3(loc[0], loc[1], loc[2])

    def update(self):
        self.sock.send(self.encode + b'loc:' + self.serialize_loc())
        msg = self.sock.recv(1024)
        if (msg[0:3] == b'ack'): print("[INFO] LOCATION UPDATED SUCCESSFULLY")
        else: print("[WARN] LOCATION UPDATE UNSUCCESSFUL")

    def get_task(self) -> Task:
        self.sock.send(self.encode + b'get')
        msg = self.sock.recv(1024)
        if msg[0] == TaskId.IDLE:
            print("[INFO] IDLE TASK RECIEVED")
            return Task(TaskId.IDLE, self.loc)
        elif msg[0] == TaskId.MOVE:
            print("[INFO] MOVE TASK RECIEVED")
            loc = self.deserialize_loc(msg[1:13])
            return Task(TaskId.MOVE, loc)
        elif msg[0] == TaskId.COLLECT:
            print("[INFO] COLLECT TASK RECIEVED")
            return Task(TaskId.COLLECT, self.loc)
        elif msg[0] == TaskId.RETURN:
            print("[INFO] RETURN TASK RECIEVED")
            return Task(TaskId.RETURN, Vec3(0, 0, 0))
        elif msg[0] == TaskId.DONE:
            print("[INFO] DONE TASK RECIEVED")
            return Task(TaskId.DONE, self.loc)
        else: return Task(TaskId.ERROR, self.loc)

    def exec_task(self, task: Task):
        if task.task == TaskId.IDLE:
            sleep(50)
        elif task.task == TaskId.MOVE or task.task == TaskId.RETURN:
            print("[INFO] MOVING TOWARDS ", task.loc)
            self.move(task.loc)
        elif task.task == TaskId.COLLECT:
            print("[INFO] COLLECTING SAMPLE")
            self.collect()
        elif task.task == TaskId.DONE:
            print("[INFO] SERVER FINISHED USING ROBOT(", self.id, ")")
            exit()
        else: # ERROR, INIT, reserved
            print("[WARN] AN UNKNOWN OR UNAVALIABLE TASK WAS SENT BY SERVER")
            self.sock.send(self.encode + b'fal')
            self.update()
            return
        self.sock.send(self.encode + b'suc')
        self.update()

    def move(self, loc:Vec3):
        sleep(500)

    def collect(self):
        sleep(500)

    def __del__(self):
        self.sock.close()
