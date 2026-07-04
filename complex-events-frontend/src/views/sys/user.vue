<template>
  <!-- 系统用户信息 -->
  <div class="user-container">
    <!-- 搜索栏 -->
    <el-card id="search">
      <el-row>
        <el-col :span="23">
          <el-input v-model="searchModel.username" clearable placeholder="用户名"></el-input>
          <el-button icon="el-icon-search" round type="primary" @click="getUserList"
            >条件查询</el-button
          >
        </el-col>
        <el-col :span="1">
          <el-button
            circle
            icon="el-icon-plus"
            type="primary"
            @click="openEditUI(null)"
          ></el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 结果列表 -->
    <el-card>
      <el-table :data="userList" stripe style="width: 100%">
        <el-table-column label="#" width="80">
          <template #default="scope">
            <!-- (pageNo-1) * pageSize + index + 1-->
            <!-- 通过作用域插槽拿到当前行的索引号 -->
            {{ (searchModel.pageNo - 1) * searchModel.pageSize + scope.$index + 1 }}
          </template>
        </el-table-column>
        <el-table-column label="用户ID" prop="id" width="100"> </el-table-column>
        <el-table-column label="用户名" prop="username" width="180"> </el-table-column>
        <el-table-column label="邮箱" prop="email" width="200"> </el-table-column>
        <el-table-column label="电话" prop="phone" width="200"></el-table-column>
        <el-table-column label="状态" prop="status" width="130"></el-table-column>
        <el-table-column align="center" header-align="center" label="头像" width="250">
          <template #default="scope">
            <el-image :src="scope.row.avatar" style="width: 40px; height: 40px"></el-image>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="scope">
            <el-button circle size="small" type="primary" @click="openEditUI(scope.row.id)">
              <el-icon>
                <Edit />
              </el-icon>
            </el-button>
            <el-button
              circle
              icon="el-icon-delete"
              size="small"
              type="danger"
              @click="deleteUser(scope.row)"
            >
              <el-icon>
                <Delete />
              </el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 分页组件 -->
    <el-pagination
      :current-page="searchModel.pageNo"
      :page-size="searchModel.pageSize"
      :page-sizes="[5, 10, 20, 50]"
      :total="total"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    >
    </el-pagination>

    <!-- 用户信息 新增/修改 对话框 -->
    <el-dialog v-model="dialogFormVisible" :title="title" @close="clearForm">
      <el-form ref="userFormRef" :model="userForm" :rules="rules">
        <el-form-item :label-width="formLabelWidth" label="用户头像">
          <!-- 文件上传地址需要修改 -->
          <el-upload
            ref="upload"
            :before-remove="beforeRemove"
            :before-upload="beforeAvatarUpload"
            :limit="1"
            :on-success="handle_success"
            action="http://localhost:9999/file/upload"
          >
            <img
              v-if="imageUrl || userForm.avatar"
              :src="userForm.avatar"
              class="avatar"
              style="width: 80px; height: 80px"
            />
            <i v-else class="el-icon-plus avatar-uploader-icon"></i>
            <div slot="tip" class="el-upload__tip">只能上传jpg/png文件,且不超过500kb</div>
          </el-upload>
        </el-form-item>

        <el-form-item :label-width="formLabelWidth" label="用户名" prop="username">
          <el-input v-model="userForm.username" autocomplete="off"></el-input>
        </el-form-item>
        <el-form-item
          v-if="userForm.id == null || userForm.id == undefined"
          :label-width="formLabelWidth"
          label="密码"
          prop="upwd"
        >
          <el-input
            v-model="userForm.password"
            autocomplete="off"
            show-password
            type="password"
          ></el-input>
        </el-form-item>
        <el-form-item :label-width="formLabelWidth" label="邮箱" prop="email">
          <el-input v-model="userForm.email" autocomplete="off"></el-input>
        </el-form-item>
        <el-form-item :label-width="formLabelWidth" label="电话号码" prop="phone">
          <el-input v-model="userForm.phone" autocomplete="off"></el-input>
        </el-form-item>
        <el-form-item :label-width="formLabelWidth" label="状态">
          <el-switch v-model="userForm.status" :active-value="1" :inactive-value="0" disabled>
          </el-switch>
        </el-form-item>
      </el-form>

      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible = false">取 消</el-button>
        <el-button type="primary" @click="saveUser">确 定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import userApi from '@/api/userApi'
import { Delete, Edit } from '@element-plus/icons-vue'

export default {
  name: 'user',
  components: {
    Edit,
    Delete,
  },
  data() {
    return {
      //表单数据
      total: 0, //总记录数
      searchModel: {
        pageNo: 1, //当前页码
        pageSize: 5, //每页显示多少条数据
      },
      userList: [],
      //弹出框数据
      title: '',
      dialogFormVisible: false, //控制对话框是否可见
      userForm: {},
      formLabelWidth: '80px',
      //表单校验规则
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 6, max: 50, message: '长度在 6 到 50 个字符', trigger: 'blur' },
        ],
        password: [
          { required: true, message: '请输入登录初始密码', trigger: 'blur' },
          { min: 6, max: 10, message: '长度在 6 到 16 个字符', trigger: 'blur' },
        ],
        phone: [{ required: true, message: '请输入电话号码', trigger: 'blur' }],
      },
      imageUrl: '',
    }
  },
  methods: {
    handleSizeChange(pageSize) {
      this.searchModel.pageSize = pageSize //更新每页显示多少条数据
      this.getUserList() //重新查询
    },
    handleCurrentChange(pageNo) {
      this.searchModel.pageNo = pageNo //更新当前页码
      this.getUserList() //重新查询
    },
    getUserList() {
      userApi.getUserList(this.searchModel).then((response) => {
        this.userList = response.data.rows //回调用户数据
        this.total = response.data.total //回调统计值
      })
    },
    //打开编辑窗口
    openEditUI(id) {
      if (id == null) {
        this.title = '新增用户'
      } else {
        this.title = '修改用户'
        //根据 id 查询用户数据
        userApi.getUserById(id).then((response) => {
          this.userForm = response.data
        })
      }
      this.dialogFormVisible = true
    },
    //关闭时清空表单
    clearForm() {
      this.userForm = {}
      this.$refs.userFormRef.clearValidate()
      this.$refs.upload.clearFiles()
      this.imageUrl = ''
    },
    //提交表单数据
    saveUser() {
      this.$refs.userFormRef.validate((valid) => {
        if (valid) {
          //验证通过把数据提交给后台
          userApi.saveUser(this.userForm).then((response) => {
            //成功提示
            this.$message({
              message: response.message,
              type: 'success',
            })
            //关闭对话框
            this.dialogFormVisible = false
            //刷新表单
            this.getUserList()
          })
        } else {
          this.$message.error('错了哦，这是一条错误消息')
        }
      })
    },
    deleteUser(user) {
      this.$confirm(`您确认删除用户 ${user.username} ?`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(() => {
          userApi.deleteUserById(user.id).then((response) => {
            this.$message({
              type: 'success',
              message: response.message,
            })
            this.getUserList()
          })
        })
        .catch(() => {
          this.$message({
            type: 'info',
            message: '已取消删除',
          })
        })
    },
    //上传图片
    handle_success(res) {
      // console.log(res.data);
      this.$message.success('图片上传成功')
      this.imageUrl = res.data
      return (this.userForm.uimg = res.data)
    },
    beforeAvatarUpload(file) {
      const isJPG = file.type === 'image/jpeg' || file.type === 'image/png'
      const isLt2M = file.size / 1024 / 1024 < 1

      if (!isJPG) {
        this.$message.error('上传头像图片只能是 JPG 或 PNG 格式!')
      }
      if (!isLt2M) {
        this.$message.error('上传头像图片大小不能超过 1MB!')
      }
      return isJPG && isLt2M
    },
    beforeRemove(file, fileList) {
      this.$confirm(`确定移除 ${file.name} ?`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(() => {
          this.imageUrl = ''
        })
        .catch(() => {
          this.$message({
            type: 'info',
            message: '已取消删除',
          })
        })
    },
  },
  created() {
    this.getUserList()
  },
}
</script>

<style></style>
