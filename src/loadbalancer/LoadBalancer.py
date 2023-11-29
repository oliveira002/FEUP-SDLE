import json
import multiprocessing

import zmq

HOST = '127.0.0.1'
FRONTEND_PORT = 6666
BACKEND_PORT = 7777


def start_task(task, *args):
    process = multiprocessing.Process(target=task, args=args)
    process.daemon = True
    process.start()


class LoadBalancer:
    def __init__(self, host=HOST, frontend_port=FRONTEND_PORT, backend_port=BACKEND_PORT):
        self.host = host
        self.frontend_port = int(frontend_port)
        self.backend_port = int(backend_port)
        self.context = zmq.Context.instance()
        self.workers = []

    def start(self):
        self.frontend = self.context.socket(zmq.ROUTER)
        self.frontend.bind(f"tcp://{self.host}:{self.frontend_port}")
        self.backend = self.context.socket(zmq.ROUTER)
        self.backend.bind(f"tcp://{self.host}:{self.backend_port}")

        self.poller = zmq.Poller()
        self.poller.register(self.frontend, zmq.POLLIN)
        self.poller.register(self.backend, zmq.POLLIN)

        while True:
            sockets = dict(self.poller.poll())

            identity = None
            message = None

            if self.frontend in sockets:
                identity, _, message = self.frontend.recv_multipart()
                identity = identity.decode("utf-8")
                message = json.loads(message.decode("utf-8"))

                print(identity, message)

                available_worker = self.workers.pop(0)
                request = [available_worker.encode("utf-8"), b"", identity.encode("utf-8"), b"", json.dumps(message).encode("utf-8")]
                self.backend.send_multipart(request)

            if self.backend in sockets:
                request = self.backend.recv_multipart()
                identity, _, message = request
                identity = identity.decode("utf-8")

                message = json.loads(message.decode("utf-8"))

                if message['type'] == 'CONNECT':
                    self.workers.append(identity)

                else:
                    request = [message['identity'].encode("utf-8"), b"", json.dumps(message).encode("utf-8")]
                    self.frontend.send_multipart(request)

                print(identity, message)



            #self.handle_message(message)

    def stop(self):
        self.backend.close()
        self.frontend.close()
        self.context.term()

    def new_task(self, task, number):
        start_task(task, number)

    def handle_message(self, message):
        # maybe handling the different types of messages here
        if message['type'] == "CONNECT":
            print(2)


def main():
    loadbalancer = LoadBalancer()
    loadbalancer.start()
    loadbalancer.stop()


if __name__ == "__main__":
    main()
