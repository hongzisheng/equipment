import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus' // 导入 Element Plus
import 'element-plus/dist/index.css' // 导入 Element Plus 的样式

import App from './App.vue'
import router from './router/index.js'
import '@/styles/index.scss'
import SvgIcon from '@/components/SvgIcon/index.vue'
import 'virtual:svg-icons-register'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import { zhCn } from 'element-plus/es/locale/index'
import { useOntologyStore } from '@/stores/ontologyStore.js'

const app = createApp(App)

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(pinia)
// 初始化本体配置数据
const ontologyStore = useOntologyStore()
ontologyStore.initData()

app.use(router)
app.use(ElementPlus, { locale: zhCn }) // 使用 Element Plus
// 全局注册 SVG 图标组件
app.component('svg-icon', SvgIcon)
app.mount('#app')
