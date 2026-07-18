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

      <el-form-item class="role-item">
        <el-radio-group v-model="loginForm.role" class="role-selector">
          <el-radio-button value="admin">管理员登录</el-radio-button>
          <el-radio-button value="worker">员工登录</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-button :loading="loading" type="primary" style="width:100%;margin-bottom:30px;" @click="handleLogin">登 录</el-button>

    </el-form>
  </div>
</template>
<script>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
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
        password: '',
        role: 'admin'
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
        if (!valid) return

        this.loading = true
        this.userStore.login(this.loginForm)
          .then(() => this.userStore.getInfo())
          .then((userInfo) => {
            const selectedRole = this.loginForm.role
            const actualRole = userInfo.role

            if (actualRole !== selectedRole) {
              // 角色不匹配，提示并重置
              const roleMap = { admin: '管理员', worker: '员工' }
              ElMessage.error(`该用户不是"${roleMap[selectedRole]}"身份，请重新选择`)
              this.userStore.resetToken()
              return
            }

            // 角色匹配，按身份跳转
            const path = selectedRole === 'admin' ? (this.redirect || '/') : '/employee'
            this.router.push({ path })
          })
          .catch((error) => {
            console.error('登录失败:', error)
          })
          .finally(() => {
            this.loading = false
          })
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
  width: min(600px, 100%);
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
    font-size: 32px;
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
    height: 54px;
    font-size: 17px;
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
  height: 54px;
  border-radius: 14px;
  font-size: 18px;
  background: linear-gradient(90deg, #4f83ff 0%, #2e64ff 100%);
  border: none;
}

.el-button:hover {
  background: linear-gradient(90deg, #5e8dff 0%, #3a79ff 100%);
}

.role-item {
  border: none !important;
  background: transparent !important;
  padding: 0 !important;
  margin-bottom: 28px !important;
  display: flex;
  justify-content: center;
}

.role-selector {
  position: relative;
  display: flex;
  width: 100%;
  padding: 4px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(6px);
}

/* 隐藏 el-radio-button 所有默认样式 */
.role-selector :deep(.el-radio-button) {
  position: relative;
  flex: 1;
}

.role-selector :deep(.el-radio-button__original-radio) {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  pointer-events: none;
}

.role-selector :deep(.el-radio-button__inner) {
  position: relative;
  z-index: 2;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 13px 16px;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: #8892a0;
  background: transparent;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  cursor: pointer;
  transition: color 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;
  line-height: 1.4;
}

.role-selector :deep(.el-radio-button__inner:hover) {
  color: #c8d0dc;
  background: transparent;
}

/* 选中态：滑块高亮 */
.role-selector :deep(.el-radio-button.is-active .el-radio-button__inner) {
  color: #ffffff;
  background: transparent;
  text-shadow: 0 0 20px rgba(79, 131, 255, 0.4);
}

/* 滑块背景 - 用伪元素模拟 */
.role-selector :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 11px 0 0 11px;
}

.role-selector :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 11px 11px 0;
}

/* 第一个选中时，滑块在左侧 */
.role-selector :deep(.el-radio-button:first-child.is-active .el-radio-button__inner)::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 11px 0 0 11px;
  background: linear-gradient(135deg, rgba(79, 131, 255, 0.25) 0%, rgba(46, 100, 255, 0.35) 100%);
  border: 1px solid rgba(79, 131, 255, 0.4);
  box-shadow:
    0 0 24px rgba(79, 131, 255, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  z-index: -1;
  animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 第二个选中时，滑块在右侧 */
.role-selector :deep(.el-radio-button:last-child.is-active .el-radio-button__inner)::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 0 11px 11px 0;
  background: linear-gradient(135deg, rgba(79, 131, 255, 0.25) 0%, rgba(46, 100, 255, 0.35) 100%);
  border: 1px solid rgba(79, 131, 255, 0.4);
  box-shadow:
    0 0 24px rgba(79, 131, 255, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  z-index: -1;
  animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 去掉 el-radio-button 之间的边框 */
.role-selector :deep(.el-radio-button + .el-radio-button) {
  margin-left: 0;
}

.role-selector :deep(.el-radio-button__inner:not(:first-child)::before) {
  display: none;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: scaleX(0.92);
  }
  to {
    opacity: 1;
    transform: scaleX(1);
  }
}
</style>
