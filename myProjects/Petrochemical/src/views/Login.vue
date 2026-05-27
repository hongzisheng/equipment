<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h2>石化设备检修调度系统</h2>
        <p>智能化、一体化的设备检修调度管理平台</p>
      </div>
      
      <!-- 登录表单 -->
      <el-form 
        v-if="!isRegister"
        ref="loginFormRef"
        :model="loginForm" 
        :rules="loginRules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            clearable
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            登录系统
          </el-button>
        </el-form-item>
        
        <div class="form-footer">
          <span>还没有账号？</span>
          <el-button type="text" @click="switchToRegister">立即注册</el-button>
        </div>
      </el-form>
      
      <!-- 注册表单 -->
      <el-form 
        v-else
        ref="registerFormRef"
        :model="registerForm" 
        :rules="registerRules"
        class="login-form"
        @keyup.enter="handleRegister"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名"
            size="large"
            clearable
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请确认密码"
            size="large"
            show-password
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="请输入邮箱"
            size="large"
            clearable
          >
            <template #prefix>
              <el-icon><Message /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item prop="phone">
          <el-input
            v-model="registerForm.phone"
            placeholder="请输入手机号"
            size="large"
            clearable
          >
            <template #prefix>
              <el-icon><Phone /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item prop="realName">
          <el-input
            v-model="registerForm.realName"
            placeholder="请输入真实姓名"
            size="large"
            clearable
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleRegister"
          >
            注册账号
          </el-button>
        </el-form-item>
        
        <div class="form-footer">
          <span>已有账号？</span>
          <el-button type="text" @click="switchToLogin">立即登录</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const loginFormRef = ref()
const registerFormRef = ref()
const loading = ref(false)
const router = useRouter()
const isRegister = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  phone: '',
  realName: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度应在3到20个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '长度应在6到20个字符之间', trigger: 'blur' }
  ]
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度应在3到20个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '长度应在6到20个字符之间', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  realName: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ]
}

function validateConfirmPassword(rule, value, callback) {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      
      try {
        const response = await request({
          url: 'http://localhost:5000/api/login',
          method: 'post',
          data: {
            username: loginForm.username,
            password: loginForm.password
          }
        })
         console.log(response)
        if (response.user.role == "admin") {
          ElMessage.success('登录成功')
          // 将token保存到localStorage
         
          localStorage.setItem('token', response.token)
          localStorage.setItem('user', JSON.stringify(response.user))
          // 登录成功后跳转到主页
          router.push('/worker-import')
        } else {
          ElMessage.error( '登录失败')
        }
      } catch (error) {
        console.error('登录错误:', error)
        ElMessage.error('登录失败，请检查用户名和密码')
      } finally {
        loading.value = false
      }
    }
  })
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      
      try {
        const response =await request({
          url: 'http://localhost:5000/api/register',
          method: 'post',
          data: {
            username: registerForm.username,
            password: registerForm.password,
            email: registerForm.email,
            phone: registerForm.phone,
            real_name: registerForm.realName,
            role: 'admin',
            company_id: 1
          }
        })
        console.log(response)
        if (response.success) {
          ElMessage.success('注册成功，请登录')
          // 注册成功后切换到登录表单
          switchToLogin()
        } else {
          ElMessage.error(response.message || '注册失败')
        }
      } catch (error) {
        console.error('注册错误:', error)
        ElMessage.error('注册失败，请稍后重试')
      } finally {
        loading.value = false
      }
    }
  })
}

const switchToRegister = () => {
  isRegister.value = true
}

const switchToLogin = () => {
  isRegister.value = false
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #ffffff;
}

.login-box {
  width: 420px;
  padding: 50px 40px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.login-box::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(
    45deg,
    rgba(102, 126, 234, 0.1),
    rgba(118, 75, 162, 0.1),
    rgba(102, 126, 234, 0.1)
  );
  z-index: 0;
  transform: rotate(45deg);
}

.login-box:hover {
  transform: translateY(-5px);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
  position: relative;
  z-index: 1;
}

.login-header h2 {
  font-size: 30px;
  color: #333;
  margin-bottom: 15px;
  font-weight: 600;
  letter-spacing: 1px;
}

.login-header p {
  font-size: 16px;
  color: #666;
  margin: 0;
  font-weight: 300;
}

.login-form {
  margin-top: 20px;
  position: relative;
  z-index: 1;
}

.login-button {
  width: 100%;
  margin-top: 20px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  letter-spacing: 2px;
  font-weight: 500;
  padding: 15px;
  border-radius: 50px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.login-button:hover {
  opacity: 0.9;
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

:deep(.el-input__wrapper) {
  border-radius: 50px;
  background: #f8f9fa;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05) !important;
  padding: 5px 15px;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.1) !important;
  background: #fff;
}

:deep(.el-form-item) {
  margin-bottom: 25px;
}

:deep(.el-form-item__label) {
  display: none;
}

:deep(.el-input__prefix) {
  padding-left: 15px;
}

:deep(.el-input__icon) {
  color: #909399;
  font-size: 18px;
}

.form-footer {
  text-align: center;
  margin-top: 20px;
  color: #666;
}

.form-footer .el-button {
  margin-left: 10px;
  font-weight: 500;
}
</style>