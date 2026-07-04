// /src/store/modules/app.js
import { defineStore } from 'pinia'
import Cookies from 'js-cookie'
import { computed, reactive, ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // state
  const sidebar = reactive({
    opened: Cookies.get('sidebarStatus') ? !!+Cookies.get('sidebarStatus') : true,
    withoutAnimation: false
  })

  const device = ref('desktop')

  // mutations/actions
  function toggleSidebar() {
    sidebar.opened = !sidebar.opened
    sidebar.withoutAnimation = false
    if (sidebar.opened) {
      Cookies.set('sidebarStatus', 1)
    } else {
      Cookies.set('sidebarStatus', 0)
    }
  }

  function closeSidebar(withoutAnimation) {
    Cookies.set('sidebarStatus', 0)
    sidebar.opened = false
    sidebar.withoutAnimation = withoutAnimation
  }

  function toggleDevice(deviceType) {
    device.value = deviceType
  }
  // getters
  const sidebarGetter = computed(() => sidebar)
  const deviceGetter = computed(() => device.value)
  return {
    // actions
    toggleSidebar,
    closeSidebar,
    toggleDevice,

    // getters
    sidebar: sidebarGetter,
    device: deviceGetter
  }
})
