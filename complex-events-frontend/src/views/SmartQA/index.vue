<template>
  <div class="smart-qa-wrapper">
    <!-- 左侧：历史对话记录栏 -->
    <div class="left-sidebar">
      <div class="sidebar-header">
        <h3 class="sidebar-title">对话记录</h3>
        <div class="sidebar-actions">
          <el-button @click="newSession" class="action-btn block-btn">
            <el-icon><Plus /></el-icon>
            新建对话
          </el-button>
          <el-button
            @click="deleteSession(activeSessionId)"
            :disabled="!activeSessionId"
            class="action-btn block-btn"
          >
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
      </div>
      <div class="session-items" v-if="chatSessions.length > 0">
        <div
          v-for="session in chatSessions"
          :key="session.id"
          :class="['session-item', { active: session.id === activeSessionId }]"
          @click="openSession(session.id)"
        >
          <div class="session-item-title">{{ session.title }}</div>
          <div class="session-item-meta">{{ formatSessionTime(session.updatedAt) }}</div>
        </div>
      </div>
      <div v-else class="empty-session">
        暂无对话记录，点击“新建对话”开始
      </div>
    </div>

    <!-- 右侧：智能问答主区域 -->
    <div class="right-main">
      <div class="chat-header">
        <h2>石化设备检修智能问答助手</h2>
        <p>基于大语言模型的智能对话系统</p>
      </div>

      <div class="chat-messages" ref="messagesRef">
        <div v-if="messages.length === 0" class="message ai-message">
          <div class="avatar">
            <el-avatar :size="40" shape="square" style="background-color: #409eff">
              <span class="avatar-text">AI</span>
            </el-avatar>
          </div>
          <div class="content">
            <div class="bubble ai-bubble">
              <p>您好！我是您的智能问答助手。</p>
              <p>我可以帮助您解答关于设备维护、调度安排等方面的问题。</p>
              <p>请随时提出您的问题，我会尽力为您解答！</p>
            </div>
          </div>
        </div>

        <div
          v-for="(msg, index) in messagesWithTimeMarkers"
          :key="index"
          :class="['message', msg.role === 'user' ? 'user-message' : 'ai-message']"
        >
          <div class="avatar" v-if="msg.role">
            <el-avatar
              :size="40"
              shape="square"
              :style="
                msg.role === 'user' ? { backgroundColor: '#67C23A' } : { backgroundColor: '#409EFF' }
              "
            >
              <span class="avatar-text">{{ msg.role === 'user' ? '您' : 'AI' }}</span>
            </el-avatar>
          </div>
          <div class="content" v-if="msg.isTimeMarker">
            <div class="message-meta time-marker">
              {{ msg.timestamp }}
            </div>
          </div>
          <div class="content" v-else>
            <div class="message-meta" v-if="msg.role === 'user' && msg.showTimestamp">
              {{ msg.timestamp }}
            </div>
            <div :class="['bubble', msg.role === 'user' ? 'user-bubble' : 'ai-bubble']">
              <template v-if="msg.role === 'user'">
                <p>{{ msg.content }}</p>
              </template>
              <template v-else>
                <div v-if="msg.isThinking" class="thinking-container">
                  <span class="thinking-text">思考中</span>
                  <span class="thinking-dots">
                    <span class="dot">.</span>
                    <span class="dot">.</span>
                    <span class="dot">.</span>
                  </span>
                </div>
                <p v-else-if="!msg.isTypingCompleted && msg.displayedContent">
                  {{ msg.displayedContent }}<span class="cursor">|</span>
                </p>
                <div v-else class="markdown-content" v-html="msg.htmlContent"></div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <div class="chat-input-area">
        <div class="input-container">
          <el-input
            v-model="inputText"
            :rows="4"
            type="textarea"
            placeholder="请输入您的问题..."
            resize="none"
            maxlength="500"
            show-word-limit
            @keydown="handleTextareaKeydown"
            class="custom-textarea"
          >
          </el-input>

          <!-- 功能选择按钮区域 -->
          <div class="function-buttons">
            <button
              v-for="(btn, index) in functionButtons"
              :key="index"
              :class="['func-btn', { active: btn.selected }]"
              @click="toggleFunction(btn)"
              :title="btn.tooltip"
            >
              <span class="btn-text">{{ btn.label }}</span>
            </button>
          </div>

          <div class="input-footer">
            <div class="char-count" v-if="inputText.length > 0">{{ inputText.length }}/500</div>
            <el-button
              type="primary"
              :disabled="!inputText.trim() || sending"
              @click="sendQuestion"
              :loading="sending"
              class="send-button-circle"
              circle
            >
              <el-icon>
                <Promotion />
              </el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Promotion, Plus, Delete } from '@element-plus/icons-vue'
import { renderMarkdown } from '@/utils/markdown.ts'

// 使用环境变量配置 API 地址（.env.development 中 VITE_APP_BASE_API=http://localhost:8800）
const apiBase = import.meta.env.VITE_APP_BASE_API

// ---------- 会话管理 ----------
const CHAT_SESSIONS_KEY = 'smart-qa-sessions'
const CHAT_ACTIVE_SESSION_KEY = 'smart-qa-active-session'

const safeSetStorage = (key, value) => {
  try {
    localStorage.setItem(key, value)
  } catch (e) {
    console.warn(`保存 ${key} 失败`, e)
  }
}

const safeGetStorage = (key) => {
  try {
    return localStorage.getItem(key)
  } catch (e) {
    console.warn(`读取 ${key} 失败`, e)
    return null
  }
}

const safeParseJSON = (value, fallback) => {
  if (!value) return fallback
  try {
    return JSON.parse(value)
  } catch (e) {
    console.warn('解析本地缓存失败', e)
    return fallback
  }
}

function generateSessionTitle(messagesList) {
  const firstUser = (messagesList || []).find((msg) => msg.role === 'user')
  if (firstUser && firstUser.content) {
    const trimmed = firstUser.content.trim()
    return trimmed.length > 24 ? `${trimmed.slice(0, 24)}...` : trimmed
  }
  return '新对话'
}

function createSession(messagesList = []) {
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    title: generateSessionTitle(messagesList),
    messages: messagesList,
    updatedAt: new Date().toISOString(),
  }
}

const chatSessions = ref([])
const activeSessionId = ref(null)

// 当前会话的消息列表（直接引用 active session 中的 messages）
const messages = computed({
  get() {
    const session = chatSessions.value.find((s) => s.id === activeSessionId.value)
    return session ? session.messages : []
  },
  set(val) {
    const session = chatSessions.value.find((s) => s.id === activeSessionId.value)
    if (session) {
      session.messages = val
    }
  },
})

function persistChatSessions() {
  safeSetStorage(CHAT_SESSIONS_KEY, JSON.stringify(chatSessions.value))
  safeSetStorage(CHAT_ACTIVE_SESSION_KEY, activeSessionId.value || '')
}

function updateCurrentSession() {
  const session = chatSessions.value.find((s) => s.id === activeSessionId.value)
  if (!session) return
  session.updatedAt = new Date().toISOString()
  session.title = generateSessionTitle(session.messages)
  persistChatSessions()
}

function openSession(id) {
  const session = chatSessions.value.find((s) => s.id === id)
  if (!session) return
  activeSessionId.value = id
  persistChatSessions()
  nextTick(() => scrollToBottom('auto'))
}

function newSession() {
  const session = createSession([])
  chatSessions.value.unshift(session)
  activeSessionId.value = session.id
  persistChatSessions()
  nextTick(() => scrollToBottom('auto'))
}

function deleteSession(id) {
  if (!id) return
  const index = chatSessions.value.findIndex((s) => s.id === id)
  if (index === -1) return
  chatSessions.value.splice(index, 1)
  if (activeSessionId.value === id) {
    if (chatSessions.value.length > 0) {
      openSession(chatSessions.value[0].id)
    } else {
      newSession()
    }
  } else {
    persistChatSessions()
  }
}

// ---------- 对话状态 ----------
const inputText = ref('')
const sending = ref(false)
const messagesRef = ref(null)

// 功能按钮配置
const functionButtons = ref([
  { id: 'rule', label: '规则库', desc: '规则库信息', selected: false, tooltip: '包含规则库信息' },
  { id: 'plan', label: '调度方案', desc: '调度方案信息', selected: false, tooltip: '包含调度方案信息' },
  { id: 'selected_workers', label: '工人信息', desc: '选中的工人信息', selected: false, tooltip: '包含选中的工人信息' },
  { id: 'maintenance_tools', label: '维修器具', desc: '维修器具信息', selected: false, tooltip: '包含维修器具信息' },
])

const toggleFunction = (button) => {
  button.selected = !button.selected
}

const getSelectedFunctions = () => {
  return functionButtons.value.reduce((acc, btn) => {
    acc[btn.id] = btn.selected ? 1 : 0
    return acc
  }, {})
}

// ---------- 消息时间标记等辅助 ----------
const messagesWithTimeMarkers = computed(() => {
  const result = []
  let lastTimestamp = 0
  for (let i = 0; i < messages.value.length; i++) {
    const currentMsg = messages.value[i]
    const currentTimestamp = new Date(currentMsg.timestampStr).getTime()
    if (currentMsg.role === 'user' && currentTimestamp - lastTimestamp > 60000) {
      result.push({
        isTimeMarker: true,
        timestamp: formatTimeDisplay(new Date(currentTimestamp)),
      })
    }
    result.push(currentMsg)
    lastTimestamp = currentTimestamp
  }
  return result
})

const formatTimeDisplay = (date) => {
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  if (isToday) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return (
    date.toLocaleDateString([], { month: 'short', day: 'numeric' }) +
    ' ' +
    date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  )
}

const formatSessionTime = (timeString) => {
  try {
    return formatTimeDisplay(new Date(timeString))
  } catch (error) {
    return timeString || ''
  }
}

// ---------- 打字机效果 ----------
let typingTimer = null
let thinkingTimer = null

const typeWriterEffect = (message, index) => {
  const content = message.content
  let charIndex = 0
  let displayedContent = ''

  if (!content || content.trim() === '') {
    messages.value[index].isTypingCompleted = true
    messages.value[index].isThinking = false
    messages.value[index].displayedContent = content
    updateCurrentSession()
    return
  }

  const startTime = Date.now()
  const maxTypingTime = 3000

  const typeNextChar = () => {
    if (charIndex < content.length && Date.now() - startTime < maxTypingTime) {
      displayedContent += content.charAt(charIndex)
      messages.value[index].displayedContent = displayedContent
      charIndex++
      scrollToBottom('auto')

      const currentChar = content.charAt(charIndex - 1)
      let delay = 3
      if (/[。，；！？、]/.test(currentChar)) {
        delay = 6
      } else if (/[.,;!?]/.test(currentChar)) {
        delay = 4.5
      } else if (currentChar === ' ') {
        delay = 1.5
      }

      typingTimer = setTimeout(typeNextChar, delay)
    } else {
      messages.value[index].displayedContent = content
      messages.value[index].isTypingCompleted = true
      messages.value[index].isThinking = false
      scrollToBottom('smooth')
      updateCurrentSession()
    }
  }

  messages.value[index].isThinking = false
  typeNextChar()
}

const startThinkingAnimation = (messageIndex) => {
  let dotIndex = 0
  const animate = () => {
    if (messages.value[messageIndex] && messages.value[messageIndex].isThinking) {
      const dots = document.querySelectorAll('.thinking-dots .dot')
      dots.forEach((dot, idx) => {
        dot.style.opacity = idx < dotIndex ? '1' : '0.3'
      })
      dotIndex = (dotIndex + 1) % 4
      thinkingTimer = setTimeout(animate, 300)
    } else {
      clearTimeout(thinkingTimer)
      const dots = document.querySelectorAll('.thinking-dots .dot')
      dots.forEach((dot) => { dot.style.opacity = '1' })
    }
  }

  setTimeout(() => {
    const dots = document.querySelectorAll('.thinking-dots .dot')
    if (dots.length > 0) animate()
  }, 50)
}

// ---------- 输入与发送 ----------
const handleTextareaKeydown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    if (!sending.value) sendQuestion()
  }
}

const sendQuestion = async () => {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  if (sending.value) return

  const userMessage = {
    role: 'user',
    content: inputText.value,
    timestamp: new Date().toLocaleTimeString(),
    timestampStr: new Date().toISOString(),
  }
  messages.value = [...messages.value, userMessage]

  const question = inputText.value
  inputText.value = ''
  sending.value = true

  const thinkingMessage = {
    role: 'ai',
    content: '',
    displayedContent: '',
    isTypingCompleted: false,
    isThinking: true,
    timestamp: new Date().toLocaleTimeString(),
    timestampStr: new Date().toISOString(),
  }
  messages.value = [...messages.value, thinkingMessage]

  await nextTick()
  scrollToBottom('smooth')

  const thinkingIndex = messages.value.length - 1
  startThinkingAnimation(thinkingIndex)

  try {
    const selectedFunctions = getSelectedFunctions()
    const response = await fetch(`${apiBase}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: question,
        ...selectedFunctions,
      }),
    })

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    const data = await response.json()

    if (data.success) {
      const idx = thinkingIndex
      messages.value[idx].content = data.reply
      messages.value[idx].htmlContent = renderMarkdown(data.reply)
      messages.value[idx].isThinking = false
      typeWriterEffect(messages.value[idx], idx)
    } else {
      throw new Error(data.error || '获取AI回复失败')
    }
  } catch (error) {
    console.error('发送失败:', error)
    ElMessage.error('发送失败，请检查后端服务是否正常运行')

    const idx = thinkingIndex
    messages.value[idx].content = '抱歉，我在处理您的问题时遇到了一些困难。请稍后再试，或者联系系统管理员。'
    messages.value[idx].isThinking = false
    typeWriterEffect(messages.value[idx], idx)
  } finally {
    sending.value = false
    updateCurrentSession()
  }
}

const scrollToBottom = (behavior = 'auto') => {
  const container = messagesRef.value
  if (!container) return
  container.scrollTo({
    top: container.scrollHeight,
    behavior,
  })
}

// ---------- 恢复会话记录 ----------
function restoreStoredMessages() {
  const cachedSessions = safeParseJSON(safeGetStorage(CHAT_SESSIONS_KEY), null)
  if (cachedSessions && Array.isArray(cachedSessions) && cachedSessions.length) {
    chatSessions.value = cachedSessions
    const activeId = safeGetStorage(CHAT_ACTIVE_SESSION_KEY)
    if (activeId && chatSessions.value.find((s) => s.id === activeId)) {
      activeSessionId.value = activeId
    } else {
      activeSessionId.value = chatSessions.value[0].id
    }
  } else {
    const initialSession = createSession([])
    chatSessions.value = [initialSession]
    activeSessionId.value = initialSession.id
    persistChatSessions()
  }

  // 将已存储的 AI 消息全部恢复为完成态
  chatSessions.value.forEach((session) => {
    session.messages = (session.messages || []).map((msg) => {
      if (msg.role === 'ai') {
        return {
          ...msg,
          isThinking: false,
          isTypingCompleted: true,
          displayedContent: msg.content || '',
          htmlContent: msg.htmlContent || renderMarkdown(msg.content || ''),
        }
      }
      return msg
    })
  })
  persistChatSessions()
}

onMounted(() => {
  restoreStoredMessages()
  nextTick(() => scrollToBottom('auto'))
})

onUnmounted(() => {
  if (typingTimer) clearTimeout(typingTimer)
  if (thinkingTimer) clearTimeout(thinkingTimer)
})
</script>

<style scoped>
.smart-qa-wrapper {
  display: flex;
  height: calc(100vh - 64px);
  min-height: 600px;
  padding: 20px;
  box-sizing: border-box;
  gap: 20px;
}

.left-sidebar {
  width: 240px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 20px 16px 12px;
  border-bottom: 1px solid #f0f3f7;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: #1e293b;
}

.sidebar-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.block-btn {
  width: 100%;
  justify-content: flex-start;
}

.action-btn {
  color: #475569;
  font-size: 13px;
}

.session-items {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}

.session-item {
  padding: 10px 12px;
  border-radius: 8px;
  background: #ffffff;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.session-item.active {
  background: #eef6ff;
  border: 1px solid #cfe4ff;
}

.session-item-title {
  font-size: 14px;
  color: #0f172a;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-item-meta {
  margin-top: 4px;
  font-size: 12px;
  color: #64748b;
}

.empty-session {
  color: #94a3b8;
  text-align: center;
  padding: 20px 16px;
  font-size: 13px;
}

.right-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  padding: 20px;
}

.chat-header {
  margin-bottom: 16px;
}

.chat-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
}

.chat-header p {
  margin: 4px 0 0;
  font-size: 14px;
  color: #64748b;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  border-radius: 12px;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 120px;
}

.message {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.user-message {
  flex-direction: row-reverse;
}

.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-text {
  font-size: 14px;
  font-weight: bold;
  color: white;
}

.content {
  display: flex;
  flex-direction: column;
  max-width: 85%;
}

.bubble {
  padding: 8px 12px;
  border-radius: 18px;
  line-height: 1.2;
  position: relative;
  word-break: break-word;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  font-size: 16px;
  min-height: 20px;
}

.user-bubble {
  background: #ecfdf5;
  color: #14532d;
}

.ai-bubble {
  background: #ffffff;
  color: #1f2937;
}

.message-meta {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 6px;
}

.time-marker {
  text-align: center;
}

.thinking-container {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #64748b;
}

.thinking-text {
  font-size: 14px;
}

.thinking-dots {
  display: inline-flex;
  gap: 2px;
}

.thinking-dots .dot {
  transition: opacity 0.2s ease;
}

.cursor {
  display: inline-block;
  animation: blink 1s step-end infinite;
}

.markdown-content {
  margin: 0;
  white-space: normal;
  word-break: break-word;
  line-height: 1.45;
  font-size: 14px;
}

.markdown-content :deep(> *:first-child) { margin-top: 0; }
.markdown-content :deep(> *:last-child) { margin-bottom: 0; }
.markdown-content :deep(p) { margin: 0 0 6px; }
.markdown-content :deep(p:last-child) { margin-bottom: 0; }
.markdown-content :deep(ul), .markdown-content :deep(ol) { margin: 4px 0 6px; padding-left: 1.1em; }
.markdown-content :deep(li) { margin: 1px 0; line-height: 1.4; }
.markdown-content :deep(li + li) { margin-top: 2px; }
.markdown-content :deep(li > p) { margin: 2px 0; }

@keyframes blink {
  50% { opacity: 0; }
}

.chat-input-area {
  margin-top: 16px;
  position: relative;
}

.custom-textarea :deep(.el-textarea__inner) {
  min-height: 100px;
  font-size: 14px;
  border-radius: 10px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  padding-right: 56px;
  padding-bottom: 42px;
}

.function-buttons {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.func-btn {
  padding: 4px 12px;
  border: 1px solid #cbd5e1;
  background: #fff;
  border-radius: 6px;
  font-size: 12px;
  color: #334155;
  cursor: pointer;
  transition: 0.2s;
}

.func-btn.active {
  background: #ecfdf5;
  border-color: #10b981;
  color: #065f46;
}

.func-btn:hover {
  background: #f1f5f9;
}

.input-footer {
  position: absolute;
  bottom: 12px;
  right: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 10;
}

.char-count {
  font-size: 12px;
  color: #94a3b8;
}

.send-button-circle {
  width: 36px;
  height: 36px;
}
</style>
