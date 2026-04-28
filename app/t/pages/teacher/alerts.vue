<template>
  <view class="container">
    <!-- 头部信息 -->
    <view class="header">
      <view class="header-left">
        <text class="title">超速报警</text>
        <text class="subtitle">校外学生速度超过80码</text>
      </view>
      <view class="header-right">
        <button class="refresh-btn" @click="loadAlerts">
          <text class="refresh-text">刷新</text>
        </button>
      </view>
    </view>
    
    <!-- 统计信息 -->
    <view class="stats-section">
      <view class="stat-item">
        <text class="stat-number">{{ alerts.length }}</text>
        <text class="stat-label">报警学生</text>
      </view>
      <view class="stat-item danger">
        <text class="stat-number">{{ seriousCount }}</text>
        <text class="stat-label">严重超速</text>
      </view>
      <view class="stat-item warning">
        <text class="stat-number">{{ warningCount }}</text>
        <text class="stat-label">一般警告</text>
      </view>
    </view>
    
    <!-- 报警列表 -->
    <view class="alerts-section">
      <view v-if="alerts.length === 0" class="empty-tip">
        <text class="empty-text">暂无超速报警</text>
        <text class="empty-subtext">系统会自动检测校外学生速度超过80码的情况</text>
      </view>
      
      <view 
        v-for="alert in alerts" 
        :key="alert.id"
        class="alert-item"
        :class="{'serious': alert.alert_level === '严重', 'warning': alert.alert_level === '警告'}"
        @click="viewOnMap(alert)"
      >
        <view class="alert-header">
          <view class="alert-student-info">
            <text class="student-name">{{ alert.student_name }}</text>
            <text class="student-id">{{ alert.student_id }}</text>
          </view>
          <view class="alert-level-badge" :class="{'serious': alert.alert_level === '严重', 'warning': alert.alert_level === '警告'}">
            {{ alert.alert_level }}
          </view>
        </view>
        
        <view class="alert-body">
          <view class="info-row">
            <text class="info-label">速度：</text>
            <text class="info-value speed">{{ alert.speed_mph }} 码</text>
            <text class="speed-convert">({{ alert.speed_mps }} m/s)</text>
          </view>
          <view class="info-row">
            <text class="info-label">班级：</text>
            <text class="info-value">{{ alert.grade }} {{ alert.class_name }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">专业：</text>
            <text class="info-value">{{ alert.major }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">位置：</text>
            <text class="info-value address">{{ alert.address }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">时间：</text>
            <text class="info-value">{{ alert.timestamp }}</text>
          </view>
        </view>
        
        <view class="alert-footer">
          <button class="action-btn view-btn" @click.stop="viewOnMap(alert)">
            查看位置
          </button>
          <button class="action-btn history-btn" @click.stop="viewHistory(alert)">
            历史轨迹
          </button>
        </view>
      </view>
    </view>
    
    <!-- 底部导航 -->
    <view class="bottom-nav">
      <button class="nav-btn" @click="goToHome">
        <text class="nav-text">返回监控</text>
      </button>
    </view>
  </view>
</template>

<script>
import config from '../../utils/config.js';

export default {
  data() {
    return {
      userInfo: {},
      SERVER_URL: config.SERVER_URL,
      alerts: []
    };
  },
  computed: {
    seriousCount() {
      return this.alerts.filter(a => a.alert_level === '严重').length;
    },
    warningCount() {
      return this.alerts.filter(a => a.alert_level === '警告').length;
    }
  },
  onLoad() {
    // 获取用户信息
    this.userInfo = uni.getStorageSync('userInfo');
    if (!this.userInfo) {
      uni.navigateTo({ url: '/pages/teacher/login' });
      return;
    }
    
    // 获取服务器URL
    const savedUrl = uni.getStorageSync('SERVER_URL');
    if (savedUrl) {
      this.SERVER_URL = savedUrl;
    }
    
    // 加载报警数据
    this.loadAlerts();
  },
  onShow() {
    // 每次显示页面时刷新数据
    this.loadAlerts();
  },
  methods: {
    // 加载超速报警数据
    loadAlerts() {
      uni.showLoading({ title: '加载中...' });
      
      uni.request({
        url: `${this.SERVER_URL}/api/get_speeding_alerts`,
        method: 'GET',
        data: {
          teacher_major: this.userInfo.major,
          teacher_department: this.userInfo.department
        },
        header: {
          'Content-Type': 'application/json'
        },
        success: (res) => {
          uni.hideLoading();
          
          if (res.data.code === 200) {
            this.alerts = res.data.data;
            // 通知教师监控页面刷新报警状态
            uni.$emit('refreshAlerts');
          } else {
            uni.showToast({ title: res.data.msg || '加载失败', icon: 'none' });
          }
        },
        fail: (err) => {
          uni.hideLoading();
          console.error('加载报警数据失败:', err);
          uni.showToast({ title: '网络错误，请稍后重试', icon: 'none' });
        }
      });
    },
    
    // 在地图上查看位置
    viewOnMap(alert) {
      // 保存当前报警信息到本地存储
      uni.setStorageSync('currentAlert', alert);
      // 返回首页并切换到地图视图
      uni.navigateBack({
        success: () => {
          // 通知首页显示该学生在地图上的位置
          uni.$emit('showStudentOnMap', {
            student_id: alert.student_id,
            latitude: alert.latitude,
            longitude: alert.longitude
          });
        }
      });
    },
    
    // 查看学生历史轨迹
    viewHistory(alert) {
      // 构造学生对象
      const student = {
        student_id: alert.student_id,
        name: alert.student_name,
        grade: alert.grade,
        department: alert.department,
        major: alert.major,
        class_name: alert.class_name
      };
      
      // 跳转到首页并打开历史轨迹弹窗
      uni.navigateBack({
        success: () => {
          setTimeout(() => {
            uni.$emit('viewStudentHistory', student);
          }, 300);
        }
      });
    },
    
    // 返回监控首页
    goToHome() {
      uni.navigateBack();
    }
  }
};
</script>

<style scoped>
.container {
  padding: 10px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding: 10px 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  flex-direction: column;
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.subtitle {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.header-right {
  display: flex;
  align-items: center;
}

.refresh-btn {
  background-color: #1a73e8;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 8px 15px;
  font-size: 14px;
}

.refresh-text {
  color: #fff;
}

/* 统计信息 */
.stats-section {
  display: flex;
  justify-content: space-around;
  margin-bottom: 10px;
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 12px;
  color: #666;
  margin-top: 5px;
}

.stat-item.danger .stat-number {
  color: #ea4335;
}

.stat-item.warning .stat-number {
  color: #fbbc04;
}

/* 报警列表 */
.alerts-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.empty-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 50px 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.empty-text {
  font-size: 16px;
  color: #666;
  margin-bottom: 10px;
}

.empty-subtext {
  font-size: 12px;
  color: #999;
  text-align: center;
}

.alert-item {
  background-color: #fff;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #999;
}

.alert-item.serious {
  border-left-color: #ea4335;
}

.alert-item.warning {
  border-left-color: #fbbc04;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.alert-student-info {
  display: flex;
  flex-direction: column;
}

.student-name {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.student-id {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.alert-level-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  color: #fff;
  background-color: #999;
}

.alert-level-badge.serious {
  background-color: #ea4335;
}

.alert-level-badge.warning {
  background-color: #fbbc04;
}

.alert-body {
  margin-bottom: 10px;
}

.info-row {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
}

.info-label {
  font-size: 13px;
  color: #666;
  width: 60px;
  flex-shrink: 0;
}

.info-value {
  font-size: 13px;
  color: #333;
  flex: 1;
}

.info-value.speed {
  color: #ea4335;
  font-weight: bold;
  font-size: 16px;
}

.speed-convert {
  font-size: 11px;
  color: #999;
  margin-left: 5px;
}

.info-value.address {
  color: #666;
  word-break: break-all;
}

.alert-footer {
  display: flex;
  gap: 10px;
  padding-top: 10px;
  border-top: 1px solid #eee;
}

.action-btn {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  text-align: center;
}

.view-btn {
  background-color: #1a73e8;
  color: #fff;
}

.history-btn {
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

/* 底部导航 */
.bottom-nav {
  margin-top: 10px;
  padding: 10px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.nav-btn {
  width: 100%;
  padding: 12px;
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.nav-text {
  color: #333;
}
</style>
