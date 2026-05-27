import request from "@/request/index";

/**
 * 使用微信登录
 * @param code
 *    微信登录成功之后返回的用户登录凭证（有效期五分钟）
 *    开发者需要在开发者服务器后台调用 auth.code2Session，使用 code 换取 openid 和 session_key 等信息
 *    auth.code2Session 接口应在服务器端调用，不可在前端（小程序、网页、APP等）直接调用
 */
export function wxLogin(code: string) {
  return request({
    url: '/wx/wxLogin',
    method: 'POST',
    data: {
      code: code
    }
  })
}

/**
 * 网页登录
 * @param username
 * @param password
 */
export function webLogin(username: string, password: string) {
  return request({
    url: '/login',
    method: 'POST',
    data:{
      username: username,
      password:password
    }
  })
}


/**
 * 绑定微信
 * @param code 绑定的微信登录的code
 * @param userId 系统里面的用户id
 */
export function wxBind(code: string,  userId: string) {
  return request({
    url: '/wx/bind',
    method: 'POST',
    data:{
      'code':code,
      'user_id':userId
    }
  })
}
