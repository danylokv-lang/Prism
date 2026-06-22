const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("node:path");
const { runPrism, checkPrismAvailable } = require("./prism-runner");

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 960,
    minHeight: 640,
    backgroundColor: "#0a0e14",
    titleBarStyle: "hiddenInset",
    trafficLightPosition: { x: 16, y: 16 },
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, "preload.js"),
    },
  });

  win.loadFile(path.join(__dirname, "index.html"));
  return win;
}

ipcMain.handle("pick-folder", async () => {
  const result = await dialog.showOpenDialog({ properties: ["openDirectory"] });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle("run-scan", (_event, targetPath) => runPrism(["scan", targetPath, "--json"]));
ipcMain.handle("run-env", (_event, targetPath) => runPrism(["env", targetPath, "--json"]));
ipcMain.handle("run-explain", (_event, targetPath) => runPrism(["explain", targetPath, "--json"]));
ipcMain.handle("check-cli", () => checkPrismAvailable());

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
