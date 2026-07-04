import request from '@/utils/request'


export default{
  // 获取用户列表
  getUserList(searchModel){
    return request({
      url: '/user',
      method: 'get',
      params: {
        pageNo: searchModel.pageNo,
        pageSize: searchModel.pageSize,
        username: searchModel.username,
      }
    })
  },
  //新增用户
  addUser(user){
    return request({
      url: '/user',
      method: 'post',
      data: user
    })
  },
  //修改用户
  updateUser(user){
    return request({
      url: '/user',
      method: 'put',
      data: user
    })
  },
  //得到某个id的用户数据
  getUserById(id){
    return request({
      url: `/user/${id}`,
      method: 'get',
    })
  },
  saveUser(user) {
    if(user.id == null && user.id == undefined){
      return this.addUser(user);
    }
    return this.updateUser(user);
  },
  //删除
  deleteUserById(id){
    return request({
      url: `/user/${id}`,
      method: 'delete',
    })
  },
  //不带参数的
  getAllUserList(){
    return request({
      url: '/user/all',
      method: 'get',
    })
  },
}
