// See the Electron documentation for details on how to use preload scripts:
// https://www.electronjs.org/docs/latest/tutorial/process-model#preload-scripts

import { contextBridge, ipcRenderer } from 'electron';
import { Party } from '../common/models';

contextBridge.exposeInMainWorld('api', {
  startBGBServer: async (party: Party): Promise<boolean> => {
    return await ipcRenderer.invoke('start-bgb-server', party);
  },
});
