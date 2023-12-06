const {app, screen, BrowserWindow} = require("electron")
const path = require('path')
const createWindow=()=>{
    const { screen } = require('electron')
    const primaryDisplay = screen.getPrimaryDisplay()
    const { width, height } = primaryDisplay.workAreaSize 
    const win = new BrowserWindow({
        width: width-400,
        height: height-200,
        webPreferences: {
            preload: path.join(__dirname, '/src/js/preload.js'),
            nodeIntegration: false,
            worldSafeExecuteJavaScript: true,
            contextIsolation: true
        }
    })

    win.loadFile("index.html")
}

require("electron-reload")(__dirname, {
    electron: path.join(__dirname, 'node_modules', '.bin', 'electron')
})

app.on("ready", createWindow)