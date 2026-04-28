<template>
  <view class="container">
    <view class="logo">
      <text class="logo-text">黄淮学院</text>
      <text class="system-text">位置管理系统</text>
    </view>
    
    <view class="btn-container">
      <button class="btn student-btn" @click="selectStudent">
        学生入口
      </button>
      <button class="btn teacher-btn" @click="selectTeacher">
        教师入口
      </button>
    </view>
    
    <view class="footer">
      <text class="footer-text">© 2026 黄淮学院 版权所有</text>
    </view>
  </view>
</template>

<script>
import config from '../../utils/config.js';

export default {
  data() {
    return {
      // 服务器配置
      SERVER_URL: config.SERVER_URL
    };
  },
  onLoad() {
    // 页面加载时检查是否已登录
    this.checkLoginStatus();
  },
  methods: {
    // 检查登录状态
    checkLoginStatus() {
      const userInfo = uni.getStorageSync('userInfo');
      if (userInfo) {
        // 如果已登录，直接跳转到对应页面
        if (userInfo.user_type === 'student') {
          uni.switchTab({ url: '/pages/student/home' });
        } else if (userInfo.user_type === 'teacher') {
          uni.switchTab({ url: '/pages/teacher/home' });
        }
      }
    },
    
    // 选择学生身份
    selectStudent() {
      uni.navigateTo({ url: '/pages/student/login' });
    },
    
    // 选择教师身份
    selectTeacher() {
      uni.navigateTo({ url: '/pages/teacher/login' });
    }
  }
};
</script>

<style scoped>
.container {
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.logo {
  margin-bottom: 60px;
  text-align: center;
}

.logo-text {
  font-size: 36px;
  font-weight: bold;
  color: #1a73e8;
  display: block;
  margin-bottom: 10px;
}

.system-text {
  font-size: 20px;
  color: #666;
  display: block;
}

.btn-container {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 60px;
}

.btn {
  height: 56px;
  line-height: 56px;
  font-size: 20px;
  border-radius: 8px;
  border: none;
  color: #fff;
  font-weight: 500;
}

.student-btn {
  background-color: #34a853;
}

.teacher-btn {
  background-color: #1a73e8;
}

.footer {
  position: absolute;
  bottom: 20px;
  text-align: center;
}

.footer-text {
  font-size: 14px;
  color: #999;
}
</style>