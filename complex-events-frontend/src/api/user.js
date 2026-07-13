export function login(data) {
  return Promise.resolve({
    code: 20000,
    data: {
      token: 'test-token-12345'
    }
  })
}

export function getInfo(token) {
  return Promise.resolve({
    code: 20000,
    data: {
      name: '管理员',
      avatar: ''
    }
  })
}

export function logout() {
  return Promise.resolve({
    code: 20000,
    message: '退出成功'
  })
}
