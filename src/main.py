from src.client.Client import Client
from src.loadbalancer.LoadBalancer import LoadBalancer
from src.server.Server import Server

NBR_CLIENTS = 1
NBR_SERVERS = 1
NBR_LOADBALANCERS = 1


def main():
    loadbalancers = []
    for i in range(NBR_LOADBALANCERS):
        loadbalancer = LoadBalancer()
        loadbalancer.start()
        loadbalancers.append(loadbalancer)

    servers = []
    for i in range(NBR_SERVERS):
        server = Server()
        server.start()
        servers.append(server)
    
    clients = []
    for i in range(NBR_CLIENTS):
        client = Client()
        client.start()
        clients.append(client)


if __name__ == "__main__":
    main()
