<template>
  <view class="container">
    <view class="title">学生登录</view>
    
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
      
      <button class="btn login-btn" @click="login">登录</button>
      
      <view class="register-link">
        <text>还没有账号？</text>
        <text class="link" @click="goToRegister">立即注册</text>
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
      // 登录信息
      username: '',
      password: ''
    };
  },
  methods: {
    // 登录
    login() {
      // 简单验证
      if (!this.username || !this.password) {
        uni.showToast({ title: '请输入用户名和密码', icon: 'none' });
        return;
      }
      
      uni.showLoading({ title: '登录中...' });
      
      // 发送登录请求
      uni.request({
        url: `${this.SERVER_URL}/api/login`,
        method: 'POST',
        data: {
          username: this.username,
          password: this.password
        },
        header: {
          'Content-Type': 'application/json'
        },
        success: (res) => {
          uni.hideLoading();
          
          if (res.data.code === 200) {
            // 登录成功，保存用户信息
            uni.setStorageSync('userInfo', res.data.data);
            uni.setStorageSync('SERVER_URL', this.SERVER_URL);
            
            // 跳转到学生主页
            uni.reLaunch({ url: '/pages/student/home' });
            uni.showToast({ title: '登录成功', icon: 'success' });
          } else {
            uni.showToast({ title: res.data.msg || '登录失败', icon: 'none' });
          }
        },
        fail: (err) => {
          uni.hideLoading();
          console.error('登录失败:', err);
          uni.showToast({ title: '网络错误，请稍后重试', icon: 'none' });
        }
      });
    },
    
    // 跳转到注册页面
    goToRegister() {
      uni.navigateTo({ url: '/pages/student/register' });
    }
  }
};
</script>

<style scoped>
.container {
  padding: 40px 20px;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.title {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  text-align: center;
  margin-bottom: 40px;
}

.form {
  background-color: #fff;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.input-group {
  margin-bottom: 25px;
}

.label {
  display: block;
  font-size: 16px;
  color: #666;
  margin-bottom: 8px;
}

.input {
  width: 100%;
  height: 48px;
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

.login-btn {
  background-color: #34a853;
}

.register-link {
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