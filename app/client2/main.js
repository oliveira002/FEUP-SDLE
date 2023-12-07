const { app, screen, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const zmq = require('zeromq');
const { v4: uuidv4 } = require('uuid');
var json = require('json');



class Client {
  constructor(mainWindow) {
    // Create a REQ socket
    this.socket = new zmq.socket("req")

    this.uuid = uuidv4();
    this.socket.identity = 'Client-' + this.uuid.toString('ascii');
    
    this.identity = this.uuid.toString('ascii');
    // Connect to the ZeroMQ endpoint
    const endpoint = 'tcp://127.0.0.1:6666';

    this.socket.connect(endpoint);

    const formattedMessage = {
        identity: this.uuid.toString(),
        body: "OI",
        type: "GET",
    };
  
      // Send the formatted message as JSON to the ZeroMQ server
    
    //this.socket.send(JSON.stringify(formattedMessage));


    this.socket.on('message', (msg) => {
      const receivedMessage = JSON.parse(msg.toString());
      console.log('Received message:', receivedMessage);

      // Send the received message to the renderer process
      mainWindow.webContents.send('zmqMessage', receivedMessage);
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

  // Handle the event from the renderer process
  ipcMain.on('getInformation', (event, arg) => {
    // Perform any necessary logic to get the information
    const information = 'FODASE';

    // Send the information back to the renderer process
    mainWindow.webContents.send('informationResponse', information);
  });

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

  mainWindow.loadFile('index.html');
  const clientBackend = new Client(mainWindow);

  // Create an instance of the Client class and pass the mainWindow reference

};

require('electron-reload')(__dirname, {
  electron: path.join(__dirname, 'node_modules', '.bin', 'electron'),
});

app.on('ready', createWindow);