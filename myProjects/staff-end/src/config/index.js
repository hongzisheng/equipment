// 后端 API 配置
const config = {
  // 开发环境使用代理，生产环境使用实际地址
  baseUrl: import.meta.env.MODE === 'production' 
    ? 'http://localhost:5000'  // 生产环境后端地址
    : '/',  // 开发环境使用 Vite 代理
  
  timeout: 10000, // 请求超时时间
}

export default config

