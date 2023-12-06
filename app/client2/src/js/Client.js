const zmq = require('zeromq');
const { uuid } = require('uuidv4');

HOST = "127.0.0.1"
PORT = "6666"
ENDPOINT = HOST+":"+PORT

class Client {
  constructor() {
    // Create a REQ socket
    this.socket = new zmq.Request

    this.uuid = uuid()
    this.socket.identity = 'Client-' + this.uuid.toString();

    this.socket.connect("tcp://"+ENDPOINT)

    // Handle messages from the ZeroMQ server
    this.socket.on('message', (msg) => {
      const receivedMessage = JSON.parse(msg.toString());
      console.log('Received message:', receivedMessage);
    });

    // Handle socket errors
    this.socket.on('error', (err) => {
      console.error(`Socket error: ${err}`);
    });

    // Handle process exit
    process.on('SIGINT', () => {
      // Close the ZeroMQ socket gracefully on process exit
      this.socket.close();
      process.exit();
    });
  }

  sendMessage(body, message_type) {
    const formattedMessage = {
      identity: this.uuid.toString(),
      body: body,
      type: message_type,
    };

    // Send the formatted message as JSON to the ZeroMQ server
    this.socket.send(JSON.stringify(formattedMessage));
  }
}
