// /src/store/modules/settings.js
import { defineStore } from 'pinia'
import defaultSettings from '@/settings.js'
import { ref } from 'vue'

const { showSettings: initialShowSettings, fixedHeader: initialFixedHeader, sidebarLogo: initialSidebarLogo } = defaultSettings

export const useSettingsStore = defineStore('settings', () => {
  // state
  const showSettings = ref(initialShowSettings)
  const fixedHeader = ref(initialFixedHeader)
  const sidebarLogo = ref(initialSidebarLogo)

  // actions
  function changeSetting(data) {
    const { key, value } = data

    // 直接修改对应的 ref 值
    if (key === 'showSettings') {
      showSettings.value = value
    } else if (key === 'fixedHeader') {
      fixedHeader.value = value
    } else if (key === 'sidebarLogo') {
      sidebarLogo.value = value
    }
  }

  return {
    // state
    showSettings,
    fixedHeader,
    sidebarLogo,

    // actions
    changeSetting
  }
})
