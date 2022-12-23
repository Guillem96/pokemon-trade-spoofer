// See the Electron documentation for details on how to use preload scripts:
// https://www.electronjs.org/docs/latest/tutorial/process-model#preload-scripts

import { contextBridge, ipcRenderer } from 'electron';
import { Party, ServerInfo } from '../common/models';

contextBridge.exposeInMainWorld('api', {
  startBGBServer: async (si: ServerInfo): Promise<boolean> => {
    si.host = si.host || '127.0.0.1';
    return await ipcRenderer.invoke('start-bgb-server', si);
  },
  uploadTradeParty: async (party: Party): Promise<boolean> => {
    return await ipcRenderer.invoke('upload-pkm-party', party);
  }
});
