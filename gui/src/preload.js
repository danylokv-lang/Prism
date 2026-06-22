const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("prismAPI", {
  pickFolder: () => ipcRenderer.invoke("pick-folder"),
  scan: (path) => ipcRenderer.invoke("run-scan", path),
  env: (path) => ipcRenderer.invoke("run-env", path),
  explain: (path) => ipcRenderer.invoke("run-explain", path),
  checkCli: () => ipcRenderer.invoke("check-cli"),
});
