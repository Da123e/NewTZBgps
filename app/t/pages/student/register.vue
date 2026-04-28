<template>
  <view class="container">
    <view class="title">学生注册</view>
    
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
        <text class="label">学号</text>
        <input 
          v-model="studentId" 
          class="input" 
          placeholder="请输入学号"
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
        <text class="label">年级</text>
        <input 
          v-model="grade" 
          class="input" 
          placeholder="请输入年级（如：2022级）"
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
        <text class="label">专业</text>
        <input 
          v-model="major" 
          class="input" 
          placeholder="请输入专业"
          type="text"
        />
      </view>
      
      <view class="input-group">
        <text class="label">班级</text>
        <input 
          v-model="className" 
          class="input" 
          placeholder="请输入班级（如：1班）"
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
      confirmPassword: '',
      studentId: '',
      name: '',
      grade: '',
      department: '',
      major: '',
      className: '',
      // 设备ID
      deviceId: ''
    };
  },
  onLoad() {
    // 初始化设备唯一标识
    this.initDeviceId();
  },
  methods: {
    // 初始化设备ID（兼容多端）
    initDeviceId() {
      // #ifdef APP-PLUS
      this.deviceId = plus.device.uuid;
      // #endif
      
      // #ifndef APP-PLUS
      // H5/小程序生成唯一标识（本地存储，避免刷新丢失）
      let deviceId = uni.getStorageSync('device_id');
      if (!deviceId) {
        deviceId = 'H5_' + Date.now() + '_' + Math.random().toString(36).substr(2, 8);
        uni.setStorageSync('device_id', deviceId);
      }
      this.deviceId = deviceId;
      // #endif
    },
    
    // 注册
    register() {
      // 简单验证
    if (!this.username || !this.password || !this.studentId || !this.name || !this.grade || !this.department || !this.major || !this.className) {
      uni.showToast({ title: '请填写所有必填项', icon: 'none' });
      return;
    }
      
      uni.showLoading({ title: '注册中...' });
      
      // 发送注册请求
      uni.request({
        url: `${this.SERVER_URL}/api/register/student`,
        method: 'POST',
        data: {
          username: this.username,
          password: this.password,
          student_id: this.studentId,
          name: this.name,
          grade: this.grade,
          department: this.department,
          major: this.major,
          class_name: this.className,
          device_id: this.deviceId
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
              uni.navigateTo({ url: '/pages/student/login' });
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
      uni.navigateTo({ url: '/pages/student/login' });
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
  background-color: #34a853;
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