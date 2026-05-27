import type { UserConfigExport } from "@tarojs/cli";
export default {

  mini: {},
  h5: {
    devServer: {
      open: false, // 关闭自动打开浏览器
      // 其他 devServer 配置...
    },
  }
} satisfies UserConfigExport<'vite'>
