const { app, screen, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const zmq = require('zeromq');
const { v4: uuidv4 } = require('uuid');
var json = require('json');
const GCounter = require("./src/js/CRDTs/GCounter");
const PNCounter = require("./src/js/CRDTs/PNCounter");
const ShoppingList = require("./src/js/CRDTs/ShoppingList");



class Client {
  constructor(mainWindow, id) {
    // Create a REQ socket
    this.socket = new zmq.socket("req")

    this.uuid = id;
    this.socket.identity = 'Client-' + this.uuid.toString('ascii');
    
    this.identity = this.uuid.toString('ascii');
    // Connect to the ZeroMQ endpoint
    const endpoint = 'tcp://127.0.0.1:6000';

    this.socket.connect(endpoint);

    const formattedMessage = {
        identity: this.uuid.toString(),
        body: "815bf169-4d4b-455f-a8b1-b9dadeaea9e3",
        type: "GET",
    };
  
      // Send the formatted message as JSON to the ZeroMQ server
    
    //this.socket.send(JSON.stringify(formattedMessage));


    this.socket.on('message', (msg) => {
      let message = JSON.parse(msg.toString());
      console.log('Received message1:', message);
      
      mainWindow.webContents.send('zmqMessage', message);
    });
    
    /*
    // Handle socket errors
    this.socket.on('error', (err) => {
      console.error(`Socket error: ${err}`);
    });

    // Handle process exit
    process.on('SIGINT', () => {
      // Close the ZeroMQ socket gracefully on process exit
      this.socket.close();
      process.exit();
    });*/
  }
}

let mainWindow; // Store reference to the main window globally

const createWindow = () => {
  const { screen } = require('electron');
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;
  mainWindow = new BrowserWindow({
    width: width - 400,
    height: height - 200,
    webPreferences: {
      preload: path.join(__dirname, '/src/js/preload.js'),
      nodeIntegration: true,
      contextIsolation: false,
      sandbox: false
    },
  });

  let clientBackend;
  ipcMain.on('frontMessage', (event, message) => {
    // Handle the message from the renderer process
    console.log('Received message from frontend:', message);
  
    const formattedMessage = {
      identity: clientBackend.identity, // Replace with your logic
      body: message.body,
      type: message.type,
    };
  
    clientBackend.socket.send(JSON.stringify(formattedMessage));
  });

  ipcMain.on('getId', (event, information) => {
    // Do something with the information
    const id = clientBackend.uuid;
    event.sender.send('getIdResponse', id); // Send a response back to the renderer
  });
  ipcMain.on('login', (event, message) => {
    // Handle the message from the renderer process
    console.log('Received message from frontend:', message);
    
      
    clientBackend = new Client(mainWindow,message.body);
    console.log("clientBackend", clientBackend);

  });

  mainWindow.loadFile('index.html');

  // Create an instance of the Client class and pass the mainWindow reference

};

require('electron-reload')(__dirname, {
  electron: path.join(__dirname, 'node_modules', '.bin', 'electron'),
});

app.on('ready', createWindow);