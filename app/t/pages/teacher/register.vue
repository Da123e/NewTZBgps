<template>
  <view class="container">
    <view class="title">教师注册</view>
    
    <view class="form">
      <view class="input-group">
        <text class="label">用户名</text>
        <input 
          v-model="username" 
          class="input" 
          placeholder="请输入用户名"
          type="text"
        />
      </view>
      
      <view class="input-group">
        <text class="label">密码</text>
        <input 
          v-model="password" 
          class="input" 
          placeholder="请输入密码"
          type="password"
        />
      </view>
      
      <view class="input-group">
        <text class="label">工号</text>
        <input 
          v-model="teacherId" 
          class="input" 
          placeholder="请输入工号"
          type="text"
        />
      </view>
      
      <view class="input-group">
        <text class="label">姓名</text>
        <input 
          v-model="name" 
          class="input" 
          placeholder="请输入姓名"
          type="text"
        />
      </view>
      
      <view class="input-group">
        <text class="label">院(系)/部</text>
        <input 
          v-model="department" 
          class="input" 
          placeholder="请输入院(系)/部"
          type="text"
        />
      </view>
      
      <view class="input-group">
        <text class="label">所授专业</text>
        <input 
          v-model="major" 
          class="input" 
          placeholder="请输入所授专业"
          type="text"
        />
      </view>
      
      <button class="btn register-btn" @click="register">注册</button>
      
      <view class="login-link">
        <text>已有账号？</text>
        <text class="link" @click="goToLogin">立即登录</text>
      </view>
    </view>
  </view>
</template>

<script>
import config from '../../utils/config.js';

export default {
  data() {
    return {
      // 服务器配置
      SERVER_URL: config.SERVER_URL,
      // 注册信息
      username: '',
      password: '',
      teacherId: '',
      name: '',
      department: '',
      major: ''
    };
  },
  methods: {
    // 注册
    register() {
      // 简单验证
      if (!this.username || !this.password || !this.teacherId || !this.name || !this.department || !this.major) {
        uni.showToast({ title: '请填写所有必填项', icon: 'none' });
        return;
      }
      
      uni.showLoading({ title: '注册中...' });
      
      // 发送注册请求
      uni.request({
        url: `${this.SERVER_URL}/api/register/teacher`,
        method: 'POST',
        data: {
          username: this.username,
          password: this.password,
          teacher_id: this.teacherId,
          name: this.name,
          department: this.department,
          major: this.major
        },
        header: {
          'Content-Type': 'application/json'
        },
        success: (res) => {
          uni.hideLoading();
          
          if (res.data.code === 200) {
            // 注册成功，跳转到登录页面
            uni.showToast({ title: '注册成功', icon: 'success' });
            setTimeout(() => {
              uni.navigateTo({ url: '/pages/teacher/login' });
            }, 1500);
          } else {
            uni.showToast({ title: res.data.msg || '注册失败', icon: 'none' });
          }
        },
        fail: (err) => {
          uni.hideLoading();
          console.error('注册失败:', err);
          uni.showToast({ title: '网络错误，请稍后重试', icon: 'none' });
        }
      });
    },
    
    // 跳转到登录页面
    goToLogin() {
      uni.navigateTo({ url: '/pages/teacher/login' });
    }
  }
};
</script>

<style scoped>
.container {
  padding: 20px;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.title {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  text-align: center;
  margin: 20px 0 30px;
}

.form {
  background-color: #fff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.input-group {
  margin-bottom: 20px;
}

.label {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 6px;
}

.input {
  width: 100%;
  height: 44px;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 0 15px;
  font-size: 16px;
  box-sizing: border-box;
}

.btn {
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 8px;
  font-size: 18px;
  font-weight: 500;
  color: #fff;
  margin-bottom: 20px;
}

.register-btn {
  background-color: #1a73e8;
}

.login-link {
  text-align: center;
  font-size: 14px;
  color: #666;
}

.link {
  color: #1a73e8;
  cursor: pointer;
  margin-left: 5px;
}
</style>