// See the Electron documentation for details on how to use preload scripts:
// https://www.electronjs.org/docs/latest/tutorial/process-model#preload-scripts

import { contextBridge, ipcRenderer } from "electron"
import { Party } from "../common/models"
import { Backends } from "../common/constants"
import { SpooferState } from "../renderer/types"

declare global {
  interface Window {
    api: {
      startBGBServer: (party: Party) => Promise<boolean>
      stopBGBServer: () => Promise<boolean>
      fetchBackendStates: () => Promise<Record<Backends, SpooferState> | null>
      isServerUp: () => Promise<{
        state: "error" | "ok" | "loading"
        message: string
      }>
      openExternalUrl: (url: string) => void
    }
  }
}

contextBridge.exposeInMainWorld("api", {
  startBGBServer: async (party: Party): Promise<boolean> => {
    return await ipcRenderer.invoke("start-bgb-server", party)
  },
  stopBGBServer: async (): Promise<boolean> => {
    return await ipcRenderer.invoke("stop-bgb-server")
  },
  fetchBackendStates: async (): Promise<Record<
    Backends,
    SpooferState
  > | null> => {
    return await ipcRenderer.invoke("fetch-backend-states")
  },
  isServerUp: async (): Promise<{
    state: "error" | "ok" | "loading"
    message: string
  }> => {
    return await ipcRenderer.invoke("is-server-up")
  },
  openExternalUrl(url: string) {
    ipcRenderer.invoke("open-external-link", url)
  },
})
