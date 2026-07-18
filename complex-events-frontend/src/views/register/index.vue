<template>
  <div class="register-container">
    <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" class="register-form" autocomplete="on" label-position="left">

      <div class="title-container">
        <h3 class="title">注册账号</h3>
      </div>

      <el-form-item prop="username">
        <span class="svg-container">
          <svg-icon icon-class="user" />
        </span>
        <el-input
          ref="usernameRef"
          v-model="registerForm.username"
          placeholder="用户名"
          name="username"
          type="text"
          tabindex="1"
          autocomplete="on"
        />
      </el-form-item>

      <el-form-item prop="real_name">
        <span class="svg-container">
          <svg-icon icon-class="user" />
        </span>
        <el-input
          v-model="registerForm.real_name"
          placeholder="姓名"
          name="real_name"
          type="text"
          tabindex="2"
          autocomplete="on"
        />
      </el-form-item>

      <el-form-item prop="email">
        <span class="svg-container">
          <svg-icon icon-class="user" />
        </span>
        <el-input
          v-model="registerForm.email"
          placeholder="邮箱（选填）"
          name="email"
          type="email"
          tabindex="3"
          autocomplete="on"
        />
      </el-form-item>

      <el-form-item prop="phone">
        <span class="svg-container">
          <svg-icon icon-class="user" />
        </span>
        <el-input
          v-model="registerForm.phone"
          placeholder="手机号"
          name="phone"
          type="text"
          tabindex="4"
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
          v-model="registerForm.password"
          :type="passwordType"
          placeholder="密码"
          name="password"
          tabindex="5"
          autocomplete="new-password"
        />
        <span class="show-pwd" @click="showPwd">
          <svg-icon :icon-class="passwordType === 'password' ? 'eye' : 'eye-open'" />
        </span>
      </el-form-item>

      <el-form-item prop="confirmPassword">
        <span class="svg-container">
          <svg-icon icon-class="password" />
        </span>
        <el-input
          v-model="registerForm.confirmPassword"
          :type="passwordType"
          placeholder="确认密码"
          name="confirmPassword"
          tabindex="6"
          autocomplete="new-password"
          @keyup.enter="handleRegister"
        />
      </el-form-item>

      <el-button :loading="loading" type="primary" style="width:100%;margin-bottom:16px;" @click="handleRegister">注 册</el-button>

      <div class="login-link">
        已有账号？
        <router-link to="/login">去登录</router-link>
      </div>

    </el-form>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { register as registerApi } from '@/api/user'

export default {
  name: 'Register',
  setup() {
    const router = useRouter()
    const registerFormRef = ref(null)
    const usernameRef = ref(null)
    const passwordRef = ref(null)

    return {
      router,
      registerFormRef,
      usernameRef,
      passwordRef,
    }
  },
  data() {
    const validateUsername = (rule, value, callback) => {
      if (value.length < 2) {
        callback(new Error('用户名至少2个字符'))
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

    const validateConfirmPassword = (rule, value, callback) => {
      if (value !== this.registerForm.password) {
        callback(new Error('两次密码不一致'))
      } else {
        callback()
      }
    }

    return {
      registerForm: {
        username: '',
        real_name: '',
        email: '',
        phone: '',
        password: '',
        confirmPassword: '',
      },
      registerRules: {
        username: [{ required: true, trigger: 'blur', validator: validateUsername }],
        real_name: [{ required: true, trigger: 'blur', message: '请输入姓名' }],
        phone: [{ required: true, trigger: 'blur', message: '请输入手机号' }],
        password: [{ required: true, trigger: 'blur', validator: validatePassword }],
        confirmPassword: [{ required: true, trigger: 'blur', validator: validateConfirmPassword }],
      },
      loading: false,
      passwordType: 'password',
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
    handleRegister() {
      this.registerFormRef.validate((valid) => {
        if (!valid) return

        this.loading = true
        const { username, real_name, email, phone, password } = this.registerForm
        registerApi({ username, real_name, email, phone, password })
          .then(() => {
            ElMessage.success('注册成功，请登录')
            this.router.push('/login')
          })
          .catch((error) => {
            console.error('注册失败:', error)
          })
          .finally(() => {
            this.loading = false
          })
      })
    },
  },
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

.register-container {
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  background-image: linear-gradient(rgba(15, 23, 32, 0), rgba(11, 18, 24, 0.85)), url('../../assets/bg.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  color: $light_gray;
  overflow: auto;
}

.register-form {
  width: min(600px, 100%);
  padding: 40px 38px 30px;
  background: $card-bg;
  border: 1px solid $border;
  border-radius: 24px;
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.32);
  backdrop-filter: blur(18px);
}

.title-container {
  margin-bottom: 24px;
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
  margin-bottom: 14px;
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
  margin-top: 10px;
  border-radius: 14px;
  font-size: 18px;
  background: linear-gradient(90deg, #4f83ff 0%, #2e64ff 100%);
  border: none;
}

.el-button:hover {
  background: linear-gradient(90deg, #5e8dff 0%, #3a79ff 100%);
}

.login-link {
  text-align: center;
  font-size: 14px;
  color: #8892a0;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  margin-top: 4px;

  a {
    color: $focus_blue;
    text-decoration: none;
    font-weight: 500;
    padding: 2px 10px;
    margin-left: 2px;
    border-radius: 6px;
    background: rgba(108, 157, 255, 0.08);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      background: rgba(108, 157, 255, 0.18);
      color: #8ab4ff;
      box-shadow: 0 0 16px rgba(108, 157, 255, 0.15);
    }
  }
}
</style>
