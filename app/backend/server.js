const zmq = require('zeromq');
const { v4: uuidv4 } = require('uuid');
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');

const app = express();
const cors = require('cors');
const server = http.createServer(app);

const io = socketIo(server, { cors: { origin: '*' } }); // Attach Socket.IO to the server

app.use(cors()); // Enable CORS for all routes

const listener = server.listen(4444, function () {
  console.log('Listening on port ' + listener.address().port);
});


class Client {
  constructor(io) {
    // Create a REQ socket
    this.socket = zmq.socket('req');

    this.uuid = uuidv4();
    this.socket.identity = 'Client-' + this.uuid.toString('ascii');

    // Connect to the ZeroMQ endpoint
    const endpoint = 'tcp://127.0.0.1:6666';
    this.socket.connect(endpoint);

    const formattedMessage = {
      identity: this.uuid.toString(),
      body: "GET",
      type: "Oi",
    };

    // Send the formatted message as JSON to the ZeroMQ server
    this.socket.send(JSON.stringify(formattedMessage));

    // Handle messages from the ZeroMQ server
    this.socket.on('message', (msg) => {
      const receivedMessage = JSON.parse(msg.toString());
      console.log('Received message:', receivedMessage);

      io.emit('zmqMessage', receivedMessage);
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

// Pass the Socket.IO instance to the Client constructor
const clientBackend = new Client(io);

io.on('connection', (socket) => {
  console.log('Client connected');

  // Handle messages from the frontend
  socket.on('frontendMessage', (message) => {
    // Process the message or send it to ZeroMQ as needed
    clientBackend.sendMessage(message.body, message.type);
  });

  socket.on('disconnect', () => {
    console.log('Client disconnected');
  });
});