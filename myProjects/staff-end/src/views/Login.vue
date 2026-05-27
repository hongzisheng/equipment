<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h2>石化设备检修调度系统</h2>
        <h3 style="font-size: 18px;color: black;font-weight: bold;margin-bottom: 10px;">员工端</h3>
        <p>智能化、一体化的设备检修调度管理平台</p>
      </div>
      
      <!-- 登录表单 -->
      <form 
        v-if="!isRegister"
        ref="loginFormRef"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <div class="form-group">
          <div class="input-wrapper">
            <i class="icon-user"></i>
            <input
              v-model="loginForm.username"
              type="text"
              placeholder="请输入用户名"
              class="form-input"
              required
            />
          </div>
        </div>
        
        <div class="form-group">
          <div class="input-wrapper">
            <i class="icon-lock"></i>
            <input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              class="form-input"
              required
            />
          </div>
        </div>
        
        <button
          type="submit"
          class="login-button"
          :disabled="loading"
        >
          <span v-if="!loading">登录系统</span>
          <span v-else class="loading-spinner"></span>
        </button>
        
        <div class="form-footer">
          <span>还没有账号？</span>
          <button type="button" class="switch-button" @click="switchToRegister">立即注册</button>
        </div>
      </form>
      
      <!-- 注册表单 -->
      <form 
        v-else
        ref="registerFormRef"
        class="login-form"
        @submit.prevent="handleRegister"
      >
        <div class="form-group">
          <div class="input-wrapper">
            <i class="icon-user"></i>
            <input
              v-model="registerForm.username"
              type="text"
              placeholder="请输入用户名"
              class="form-input"
              required
            />
          </div>
        </div>
        
        <div class="form-group">
          <div class="input-wrapper">
            <i class="icon-lock"></i>
            <input
              v-model="registerForm.password"
              type="password"
              placeholder="请输入密码"
              class="form-input"
              required
            />
          </div>
        </div>
        
        <div class="form-group">
          <div class="input-wrapper">
            <i class="icon-lock"></i>
            <input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请确认密码"
              class="form-input"
              required
            />
          </div>
        </div>
        
        <div class="form-group">
          <div class="input-wrapper">
            <i class="icon-email"></i>
            <input
              v-model="registerForm.email"
              type="email"
              placeholder="请输入邮箱"
              class="form-input"
              required
            />
          </div>
        </div>
        
        <div class="form-group">
          <div class="input-wrapper">
            <i class="icon-phone"></i>
            <input
              v-model="registerForm.phone"
              type="tel"
              placeholder="请输入手机号"
              class="form-input"
              required
            />
          </div>
        </div>
        
        <div class="form-group">
          <div class="input-wrapper">
            <i class="icon-user"></i>
            <input
              v-model="registerForm.realName"
              type="text"
              placeholder="请输入真实姓名"
              class="form-input"
              required
            />
          </div>
        </div>
        
        <button
          type="submit"
          class="login-button"
          :disabled="loading"
        >
          <span v-if="!loading">注册账号</span>
          <span v-else class="loading-spinner"></span>
        </button>
        
        <div class="form-footer">
          <span>已有账号？</span>
          <button type="button" class="switch-button" @click="switchToLogin">立即登录</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

// 保留原有的响应式引用
const loginFormRef = ref()
const registerFormRef = ref()
const loading = ref(false)
const router = useRouter()
const isRegister = ref(false)

// 保留原有的表单数据模型
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

const handleLogin = async () => {
  // 验证表单
  if (!loginForm.username || !loginForm.password) {
    ElMessage.error('请填写完整信息')
    return
  }
  
  if (loginForm.username.length < 3 || loginForm.username.length > 20) {
    ElMessage.error('用户名长度应在3到20个字符之间')
    return
  }
  
  if (loginForm.password.length < 6 || loginForm.password.length > 20) {
    ElMessage.error('密码长度应在6到20个字符之间')
    return
  }
  
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
    if (response.user.role === 'worker') {
      localStorage.setItem('token', response.token)
      localStorage.setItem('user', JSON.stringify(response.user))
      localStorage.setItem('isLoggedIn', true)
      router.push('/schedule')
    } 
  } catch (error) {
    console.error('登录错误:', error)
    
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  // 验证表单
  if (!registerForm.username || !registerForm.password || !registerForm.confirmPassword || 
      !registerForm.email || !registerForm.phone || !registerForm.realName) {
    ElMessage.error('请填写完整信息')
    return
  }
  
  if (registerForm.username.length < 3 || registerForm.username.length > 20) {
    ElMessage.error('用户名长度应在3到20个字符之间')
    return
  }
  
  if (registerForm.password.length < 6 || registerForm.password.length > 20) {
    ElMessage.error('密码长度应在6到20个字符之间')
    return
  }
  
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(registerForm.email)) {
    ElMessage.error('请输入正确的邮箱地址')
    return
  }
  
  const phoneRegex = /^1[3-9]\d{9}$/
  if (!phoneRegex.test(registerForm.phone)) {
    ElMessage.error('请输入正确的手机号')
    return
  }
  
  loading.value = true
  
  try {
    const response = await request({
      url: 'http://localhost:5000/api/register',
      method: 'post',
      data: {
        username: registerForm.username,
        password: registerForm.password,
        email: registerForm.email,
        phone: registerForm.phone,
        real_name: registerForm.realName,
        role: 'worker',
        company_id: 1
      }
    })
    
    if (response.success) {
      ElMessage.success('注册成功，请登录')
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
  min-height: 100vh;
  width: 100vw;
  background: #ffffff;
  position: fixed;
  top: 0;
  left: 0;
  overflow: hidden;
}

.login-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 10% 20%, rgba(102, 126, 234, 0.05) 0%, transparent 20%),
              radial-gradient(circle at 90% 80%, rgba(118, 75, 162, 0.05) 0%, transparent 20%),
              radial-gradient(circle at 50% 50%, rgba(102, 126, 234, 0.03) 0%, transparent 30%);
  z-index: 1;
}

.login-box {
  width: 100%;
  max-width: 450px;
  padding: 50px 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  position: relative;
  z-index: 2;
  margin: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.login-box:hover {
  transform: translateY(-5px);
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.3);
  background: rgba(255, 255, 255, 0.98);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
  position: relative;
}

.login-header h2 {
  font-size: 28px;
  color: #333;
  margin-bottom: 15px;
  font-weight: 700;
  letter-spacing: 1px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.login-header p {
  font-size: 16px;
  color: #666;
  margin: 0;
  font-weight: 400;
}

.login-form {
  margin-top: 20px;
}

.form-group {
  margin-bottom: 25px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-wrapper i {
  position: absolute;
  left: 15px;
  color: #909399;
  font-size: 18px;
  z-index: 2;
}

.form-input {
  width: 100%;
  padding: 16px 20px 16px 50px;
  border: 2px solid transparent;
  border-radius: 50px;
  background: rgba(248, 249, 250, 0.8);
  font-size: 16px;
  color: #333;
  transition: all 0.3s ease;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.08);
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 20px 0 rgba(102, 126, 234, 0.2);
  transform: translateY(-2px);
}

.form-input:hover {
  background: rgba(255, 255, 255, 0.9);
  border-color: rgba(102, 126, 234, 0.3);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.12);
}

.login-button {
  width: 100%;
  padding: 16px;
  margin-top: 20px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  border-radius: 50px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 2px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  position: relative;
  overflow: hidden;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
  background: linear-gradient(135deg, #5a6fd8, #6a4190);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.form-footer {
  text-align: center;
  margin-top: 25px;
  color: #666;
  font-size: 14px;
}

.switch-button {
  background: none;
  border: none;
  color: #667eea;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 15px;
  transition: all 0.3s ease;
  margin-left: 5px;
}

.switch-button:hover {
  background: rgba(102, 126, 234, 0.1);
  color: #5a6fd8;
}

/* 图标字体 */
.icon-user::before {
  content: "👤";
}

.icon-lock::before {
  content: "🔒";
}

.icon-email::before {
  content: "✉️";
}

.icon-phone::before {
  content: "📱";
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-box {
    margin: 10px;
    padding: 40px 30px;
  }
  
  .login-header h2 {
    font-size: 24px;
  }
  
  .form-input {
    padding: 14px 18px 14px 45px;
    font-size: 15px;
  }
}

@media (max-width: 480px) {
  .login-box {
    padding: 30px 20px;
    margin: 5px;
  }
  
  .login-header h2 {
    font-size: 22px;
  }
  
  .login-button {
    padding: 14px;
    font-size: 15px;
  }
}
</style>