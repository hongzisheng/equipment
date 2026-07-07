declare module '@/commomComponents/*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module '@/commomComponents/*' {
  const content: any
  export default content
}

declare module '@/api/statisticApi' {
  const content: any
  export default content
}

declare module '@/api/streamingApi' {
  const content: any
  export default content
}

declare module '@/api/systemApi' {
  const content: any
  export default content
}

declare module 'vis-network/declarations/network/Network.js' {
  const content: any
  export default content
}

declare module 'mind-elixir/dist/types/interact' {
  const content: any
  export default content
}
