import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons'
import sassDts from 'vite-plugin-sass-dts'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({

  // 基础公共路径
  base: './',

  // 开发服务器配置
  server: {
    port: 8889,
    open: false,
    proxy: {
      '/api': {
        target: 'http://localhost:8800',
        changeOrigin: true
      },
      '/user': {
        target: 'http://localhost:8800',
        changeOrigin: true
      },
      '/data': {
        target: 'http://localhost:8800',
        changeOrigin: true
      },
      '/process': {
        target: 'http://localhost:8800',
        changeOrigin: true
      },
      '/info': {
        target: 'http://localhost:8800',
        changeOrigin: true
      }
    }
  },

  // 插件配置
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // 保留空白字符
          whitespace: 'preserve'
        }
      }
    }),
    vueDevTools(),
    createSvgIconsPlugin({
      iconDirs: [path.resolve(process.cwd(), 'src/icons/svg')],
      symbolId: 'icon-[name]',
    }),
    sassDts(),
  ],
  // 解析配置

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },

  // CSS 配置
  css: {
    // 可根据需要添加预处理器配置
  },

  // 构建优化配置
  build: {
    outDir: 'dist',
    assetsDir: 'static',
    rollupOptions: {
      output: {
        manualChunks: {
          // 分包配置
          'vue-runtime': ['vue', 'vue-router', 'pinia'],
          'element-plus': ['element-plus']
        }
      }
    }
  }
})
