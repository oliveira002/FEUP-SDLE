# FEUP-SDLE

## Check list

### Load balancers
- [x] Load balancers can swap between active and passive
- [x] Both load balancers have the same hash ring at all times
    - [x] Primary active and backup passive
    - [x] Backup active and primary passive
    - [x] Primary active and backup passive, after backup restart

### Servers
- [x] Servers can connect to back up load balancer when primary is down
- [ ] Servers can merge POST data with local data
- [x] Servers can persist data
- [x] Servers can reply to GET requests
- [ ] Servers can replicate data to other servers
- [ ] Servers can hand off data when a supposed server is down
- [ ] Servers can rebalance the hash ring when a new server is added. We assume that when a server goes down, it will come back up
- [x] Servers reply with 404 to non-existent shopping list

### Clients
- [x] Clients can connect to the backup load balancer when primary is down
- [x] Clients can differentiate between server issues and load balancer issues
- [x] Clients can send POST requests
- [x] Clients can send GET requests
- [ ] Clients can merge GET data with local data
- [ ] Clients can persist data locally
- [ ] Clients can get new shopping lists by their pre-given ID

### CRDTs
- [ ] Property testing