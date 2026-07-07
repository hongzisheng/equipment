<template>
  <div class="login-container">
    <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" class="login-form" autocomplete="on" label-position="left">

      <div class="title-container">
        <h3 class="title">欢迎使用设备调度系统</h3>
      </div>

      <el-form-item prop="username">
        <span class="svg-container">
          <svg-icon icon-class="user" />
        </span>
        <el-input
          ref="usernameRef"
          v-model="loginForm.username"
          placeholder="用户名"
          name="username"
          type="text"
          tabindex="1"
          autocomplete="on"
        />
      </el-form-item>

      <el-form-item prop="password">
        <span class="svg-container">
          <svg-icon icon-class="password" />
        </span>
        <el-input
          :key="passwordType"
          ref="passwordRef"
          v-model="loginForm.password"
          :type="passwordType"
          placeholder="密码"
          name="password"
          tabindex="2"
          autocomplete="on"
          @keyup.enter="handleLogin"
        />
        <span class="show-pwd" @click="showPwd">
          <svg-icon :icon-class="passwordType === 'password' ? 'eye' : 'eye-open'" />
        </span>
      </el-form-item>

      <el-button :loading="loading" type="primary" style="width:100%;margin-bottom:30px;" @click="handleLogin">登 录</el-button>

    </el-form>
  </div>
</template>
<script>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { validUsername } from '@/utils/validate'
import { useUserStore } from '@/stores/user'

export default {
  name: 'Login',
  setup() {
    // 使用 Vue 3 Composition API 获取路由和路由器实例
    const router = useRouter()
    const route = useRoute()

    // 使用 Pinia store
    const userStore = useUserStore()

    // 定义模板引用
    const loginFormRef = ref(null)
    const usernameRef = ref(null)
    const passwordRef = ref(null)

    return {
      loginFormRef,
      usernameRef,
      passwordRef,
      router,
      route,
      userStore
    }
  },
  data() {
    // 验证规则
    const validateUsername = (rule, value, callback) => {
      if (!validUsername(value)) {
        callback(new Error('请输入正确的用户名'))
      } else {
        callback()
      }
    }

    const validatePassword = (rule, value, callback) => {
      if (value.length < 6) {
        callback(new Error('密码不少于6位'))
      } else {
        callback()
      }
    }

    return {
      // 测试的时候默认输入
      loginForm: {
        username: '',
        password: ''
      },
      loginRules: {
        username: [{ required: true, trigger: 'blur', validator: validateUsername }],
        password: [{ required: true, trigger: 'blur', validator: validatePassword }]
      },
      loading: false,
      passwordType: 'password',
      redirect: undefined
    }
  },
  watch: {
    route: {
      handler: function(newRoute) {
        this.redirect = newRoute.query && newRoute.query.redirect
      },
      immediate: true
    }
  },
  methods: {
    showPwd() {
      if (this.passwordType === 'password') {
        this.passwordType = ''
      } else {
        this.passwordType = 'password'
      }
      this.$nextTick(() => {
        this.passwordRef.focus()
      })
    },
    handleLogin() {
      console.log('handleLogin')
      this.loginFormRef.validate((valid) => {
        if (valid) {
          this.loading = true
          // 使用 Pinia store 替代 Vuex
          this.userStore.login(this.loginForm).then(() => {
            // 修复：使用 this.router 而不是 useRouter()
            this.router.push({ path: this.redirect || '/' })
            this.loading = false
          }).catch(() => {
            this.loading = false
          })
        } else {
          console.log('error submit!!')
          return false
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
$bg: #0f1720;
$card-bg: rgba(255, 255, 255, 0.08);
$border: rgba(255, 255, 255, 0.16);
$input-bg: rgba(255, 255, 255, 0.08);
$input-border: rgba(255, 255, 255, 0.18);
$light_gray: #eef2f7;
$muted_gray: #9aa5b1;
$focus_blue: #6c9dff;

.login-container {
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
  background-image: linear-gradient(rgba(15, 23, 32, 0), rgba(11, 18, 24, 0.85)), url('../../assets/bg.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  color: $light_gray;
  overflow: hidden;
}

.login-form {
  width: min(520px, 100%);
  padding: 44px 38px 34px;
  background: $card-bg;
  border: 1px solid $border;
  border-radius: 24px;
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.32);
  backdrop-filter: blur(18px);
}

.title-container {
  margin-bottom: 28px;
  text-align: center;

  .title {
    font-size: 28px;
    color: #f8fafc;
    margin: 0;
    font-weight: 700;
    letter-spacing: 0.03em;
  }
}

.el-form-item {
  margin-bottom: 22px;
  padding: 4px 8px;
  border-radius: 16px;
  background: $input-bg;
  border: 1px solid $input-border;
  position: relative;
}

.el-input {
  width: 100%;

  .el-input__wrapper {
    background: transparent;
    border: 0;
    box-shadow: none;
  }

  input {
    width: 100%;
    background: transparent;
    border: 0;
    color: $light_gray;
    padding: 14px 12px 14px 52px;
    height: 50px;
    font-size: 15px;
    caret-color: $focus_blue;

    &:-webkit-autofill {
      box-shadow: 0 0 0px 1000px $input-bg inset !important;
      -webkit-text-fill-color: $light_gray !important;
    }
  }
}

.svg-container {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  color: $muted_gray;
}

.show-pwd {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 16px;
  color: $muted_gray;
  cursor: pointer;
}

.el-button {
  width: 100%;
  height: 50px;
  border-radius: 14px;
  font-size: 16px;
  background: linear-gradient(90deg, #4f83ff 0%, #2e64ff 100%);
  border: none;
}

.el-button:hover {
  background: linear-gradient(90deg, #5e8dff 0%, #3a79ff 100%);
}
</style>
