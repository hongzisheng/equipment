// /src/store/modules/user.js
import { defineStore } from 'pinia'
import { login as loginApi, logout as logoutApi, getInfo as getInfoApi } from '@/api/user'
import { getToken, setToken, removeToken } from '@/utils/auth'
import { computed, ref } from 'vue'

const getDefaultState = () => {
  return {
    token: getToken(),
    name: '',
    avatar: '',
    role: '',
  }
}

export const useUserStore = defineStore(
  'user',
  () => {
    // state
    const token = ref(getToken())
    const name = ref('')
    const avatar = ref('')
    const role = ref('')

    // actions
    function resetState() {
      const defaultState = getDefaultState()
      token.value = defaultState.token
      name.value = defaultState.name
      avatar.value = defaultState.avatar
      role.value = defaultState.role
    }

    function setTokenAction(tokenValue) {
      token.value = tokenValue
    }

    function setName(nameValue) {
      name.value = nameValue
    }

    function setAvatar(avatarValue) {
      avatar.value = avatarValue
    }

    function setRole(roleValue) {
      role.value = roleValue
    }

    // user login
    async function login(userInfo) {
      const { username, password } = userInfo
      return new Promise((resolve, reject) => {
        loginApi({ username: username.trim(), password: password })
          .then((response) => {
            const { data } = response
            setTokenAction(data.token)
            setToken(data.token)
            resolve()
          })
          .catch((error) => {
            reject(error)
          })
      })
    }

    // get user info
    function getInfo() {
      return new Promise((resolve, reject) => {
        getInfoApi()
          .then((response) => {
            const { data } = response

            if (!data) {
              reject('Verification failed, please Login again.')
            }

            const { name: userName, avatar: userAvatar, role: userRole } = data

            setName(userName)
            setAvatar(userAvatar)
            setRole(userRole || '')
            resolve(data)
          })
          .catch((error) => {
            reject(error)
          })
      })
    }

    // user logout
    function logout() {
      return new Promise((resolve, reject) => {
        logoutApi()
          .then(() => {
            removeToken() // must remove token first
            resetRouter()
            resetState()
            resolve()
          })
          .catch((error) => {
            reject(error)
          })
      })
    }

    // remove token
    function resetToken() {
      return new Promise((resolve) => {
        removeToken() // must remove token first
        resetState()
        resolve()
      })
    }

    const nameGetter = computed(() => name.value)
    const avatarGetter = computed(() => avatar.value)
    const tokenGetter = computed(() => token.value)
    const roleGetter = computed(() => role.value)
    return {
      // getter
      token: tokenGetter,
      name: nameGetter,
      avatar: avatarGetter,
      role: roleGetter,

      // actions
      login,
      getInfo,
      logout,
      resetToken,
    }
  },
  {
    persist: true,
  },
)
