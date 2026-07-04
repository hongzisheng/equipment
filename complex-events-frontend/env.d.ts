/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_BASE_API:string
  readonly VITE_APP_MAPBOX_TOKEN:string
  readonly VITE_APP_TIANDITU_TOKEN: string
  // 可根据需要添加其他环境变量
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
