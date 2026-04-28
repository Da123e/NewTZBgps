<template>
  <view class="container">
    <!-- 头部信息 -->
    <view class="header">
      <view class="header-left">
        <text class="welcome">欢迎，{{ userInfo.name }}</text>
        <text class="teacher-id">工号：{{ userInfo.teacher_id }}</text>
      </view>
      <view class="header-right">
        <button 
          class="alert-btn" 
          :class="{'blink': isAlertBlinking}"
          @click="goToAlerts"
        >
          <text class="alert-text">报警</text>
          <text v-if="alertCount > 0" class="alert-badge">{{ alertCount }}</text>
        </button>
        <button class="refresh-btn" @click="refreshStudents">
          <text class="refresh-text">刷新</text>
        </button>
      </view>
    </view>
    
    <!-- 筛选条件 -->
    <view class="filter-section">
      <view class="filter-row">
        <view class="filter-item">
          <text class="filter-label">年级</text>
          <input 
            v-model="filter.grade" 
            class="filter-input" 
            placeholder="请输入年级"
          />
        </view>
        <view class="filter-item">
          <text class="filter-label">院(系)/部</text>
          <input 
            v-model="filter.department" 
            class="filter-input" 
            placeholder="请输入院(系)/部"
          />
        </view>
      </view>
      <view class="filter-row">
        <view class="filter-item">
          <text class="filter-label">专业</text>
          <input 
            v-model="filter.major" 
            class="filter-input" 
            placeholder="请输入专业"
          />
        </view>
        <view class="filter-item">
          <text class="filter-label">学号</text>
          <input 
            v-model="filter.studentId" 
            class="filter-input" 
            placeholder="请输入学号"
          />
        </view>
      </view>
      <button class="btn filter-btn" @click="queryStudents">筛选</button>
    </view>
    
    <!-- 视图切换标签 -->
    <view class="view-tabs">
      <button 
        class="tab-btn" 
        :class="{active: activeView === 'map'}" 
        @click="activeView = 'map'"
      >
        地图视图
      </button>
      <button 
        class="tab-btn" 
        :class="{active: activeView === 'list'}" 
        @click="activeView = 'list'"
      >
        列表视图
      </button>
    </view>
    
    <!-- 地图视图 -->
    <view v-if="activeView === 'map' && !showHistoryModal" class="map-section map-fullscreen">
      <view class="map-wrapper">
        <map 
          id="mainMap" 
          class="map map-expand" 
          :latitude="mainMapCenter.latitude"
          :longitude="mainMapCenter.longitude"
          :scale="15"
          :markers="mainMapMarkers"
          :polyline="mainMapPolylines"
          :provider="'amap'"
          show-location
          @markertap="onMarkerTap"
        ></map>
        <!-- 学生信息卡片 -->
        <view v-if="selectedStudent" class="student-info-card">
          <view class="card-header">
            <text class="card-title">学生信息</text>
            <text class="card-close" @click="selectedStudent = null">×</text>
          </view>
          <view class="card-body">
            <view class="info-row">
              <text class="info-label">姓名：</text>
              <text class="info-value">{{ selectedStudent.name }}</text>
            </view>
            <view class="info-row">
              <text class="info-label">学号：</text>
              <text class="info-value">{{ selectedStudent.student_id }}</text>
            </view>
            <view class="info-row">
              <text class="info-label">专业：</text>
              <text class="info-value">{{ selectedStudent.major }}</text>
            </view>
            <view class="info-row">
              <text class="info-label">年级：</text>
              <text class="info-value">{{ selectedStudent.grade }}</text>
            </view>
            <view class="info-row">
              <text class="info-label">班级：</text>
              <text class="info-value">{{ selectedStudent.class_name || '未设置' }}</text>
            </view>
            <view class="info-row">
              <text class="info-label">状态：</text>
              <text class="info-value" :class="{'in-campus': selectedStudent.location?.is_on_campus, 'out-campus': !selectedStudent.location?.is_on_campus}">
                {{ selectedStudent.location?.campus_status || '未知' }}
              </text>
            </view>
            <view v-if="selectedStudent.location?.speed" class="info-row">
              <text class="info-label">速度：</text>
              <text 
                class="info-value"
                :class="{'speed-over': selectedStudent.location.speed >= 35.76, 'speed-normal': selectedStudent.location.speed < 35.76}"
              >
                {{ selectedStudent.location.speed }} m/s ({{ (selectedStudent.location.speed / 0.44704).toFixed(0) }} 码)
              </text>
            </view>
            <view class="info-row">
              <text class="info-label">更新时间：</text>
              <text class="info-value">{{ selectedStudent.location?.timestamp || '暂无数据' }}</text>
            </view>
          </view>
          <view class="card-footer">
            <button class="view-history-btn" @click="viewStudentHistory(selectedStudent)">查看历史轨迹</button>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 列表视图 -->
    <view v-if="activeView === 'list'" class="student-section">
      <view class="section-title">学生列表</view>
      <view class="student-list">
        <view 
          v-for="student in students" 
          :key="student.student_id"
          class="student-item"
          @click="viewStudentHistory(student)"
        >
          <view class="student-info">
            <text class="student-name">{{ student.name }}</text>
            <text class="student-id">{{ student.student_id }}</text>
            <view class="student-detail">
              <text>{{ student.grade }}</text>
              <text class="separator">|</text>
              <text>{{ student.department }}</text>
              <text class="separator">|</text>
              <text>{{ student.major }}</text>
              <text class="separator">|</text>
              <text>{{ student.class_name || '未设置' }}</text>
            </view>
          </view>
          <view class="student-status">
            <view class="location-status" :class="{'in-campus': student.location.is_on_campus === true, 'out-campus': student.location.is_on_campus === false}">
              {{ student.location.campus_status }}
            </view>
            <text 
              v-if="student.location.speed" 
              class="speed-info"
              :class="{'speed-over': student.location.speed >= 35.76, 'speed-normal': student.location.speed < 35.76}"
            >
              {{ student.location.speed }} m/s ({{ (student.location.speed / 0.44704).toFixed(0) }} 码)
            </text>
            <text class="update-time">{{ student.location.timestamp || '暂无数据' }}</text>
          </view>
        </view>
        
        <!-- 空数据提示 -->
        <view v-if="students.length === 0" class="empty-tip">
          <text>暂无学生数据</text>
        </view>
      </view>
    </view>
    
    <!-- 学生历史位置弹窗 -->
    <view class="modal" v-if="showHistoryModal">
      <view class="modal-content">
        <view class="modal-header">
          <text class="modal-title">{{ currentStudent.name }} 的位置历史</text>
          <view class="modal-header-right">
            <!-- 时间筛选器 -->
            <view class="time-filter">
              <picker 
                mode="selector" 
                :range="timeFilterOptions" 
                :value="timeFilterIndex"
                @change="onTimeFilterChange"
              >
                <view class="picker-view">
                  <text class="picker-text">{{ timeFilterOptions[timeFilterIndex] }}</text>
                  <text class="picker-arrow">▼</text>
                </view>
              </picker>
            </view>
            <view class="view-toggle">
              <button 
                class="toggle-btn" 
                :class="{active: viewMode === 'list'}" 
                @click="viewMode = 'list'"
              >
                列表
              </button>
              <button 
                class="toggle-btn" 
                :class="{active: viewMode === 'map'}" 
                @click="viewMode = 'map'"
              >
                地图
              </button>
            </view>
            <text class="modal-close" @click="closeHistoryModal">×</text>
          </view>
        </view>
        <view class="modal-body">
          <!-- 列表视图 -->
          <view v-if="viewMode === 'list'" class="history-list">
            <view 
              v-for="record in locationHistory" 
              :key="record.id"
              class="history-item"
            >
              <view class="history-time">{{ record.timestamp }}</view>
              <view class="history-location">
                <text class="location-coord">{{ record.latitude }}, {{ record.longitude }}</text>
                <text class="location-address">{{ record.address }}</text>
              </view>
              <view class="history-info">
                <view class="history-status" :class="{'in-campus': record.is_on_campus === true, 'out-campus': record.is_on_campus === false}">
                  {{ record.campus_status }}
                </view>
                <text 
                  v-if="record.speed" 
                  class="history-speed"
                  :class="{'speed-over': record.speed >= 35.76, 'speed-normal': record.speed < 35.76}"
                >
                  {{ record.speed }} m/s ({{ (record.speed / 0.44704).toFixed(0) }} 码)
                </text>
              </view>
            </view>
          </view>
          
          <!-- 地图视图 -->
          <view v-if="viewMode === 'map'" class="map-container">
            <map 
              id="map" 
              class="map" 
              :style="{height: mapHeight + 'px'}"
              :latitude="mapCenter.latitude"
              :longitude="mapCenter.longitude"
              :scale="15"
              :polyline="polyline"
              :markers="markers"
              :provider="'amap'"
              show-location
            ></map>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import config from '../../utils/config.js';

export default {
  data() {
    return {
      // 用户信息
      userInfo: {},
      // 服务器配置
      SERVER_URL: config.SERVER_URL,
      // 学生列表
      students: [],
      // 筛选条件
      filter: {
        grade: '',
        department: '',
        major: '',
        studentId: ''
      },
      // 学生位置历史
      showHistoryModal: false,
      currentStudent: {},
      locationHistory: [],
      // 视图模式：list 或 map
      viewMode: 'list',
      // 地图高度
      mapHeight: 500,
      // 地图上下文
      mapContext: null,
      // 地图中心点（黄淮学院北区）
      mapCenter: {
        latitude: 33.0105,
        longitude: 114.0065
      },
      // 轨迹线
      polyline: [],
      // 标记点
      markers: [],
      // 时间筛选选项
      timeFilterOptions: ['全部', '最近1小时', '最近3小时', '最近6小时', '最近12小时', '最近1天', '最近3天', '最近7天'],
      // 当前时间筛选索引
      timeFilterIndex: 0,
      // 原始位置历史数据（未筛选）
      originalLocationHistory: [],
      // 主地图配置
      mainMapHeight: 400,
      mainMapCenter: {
        latitude: 33.0105,
        longitude: 114.0065
      },
      mainMapMarkers: [],
      mainMapPolylines: [],
      // 学生颜色映射
      studentColors: ['#1a73e8', '#ea4335', '#34a853', '#fbbc04', '#9c27b0', '#ff6d00', '#00acc1', '#795548'],
      // 活动视图：map 或 list
      activeView: 'map',
      // 选中的学生（地图标记点击）
      selectedStudent: null,
      // 报警数量
      alertCount: 0,
      // 报警闪烁定时器
      alertBlinkTimer: null,
      // 是否显示闪烁效果
      isAlertBlinking: false,
      // 上次查看报警的时间
      lastAlertCheckTime: null
    };
  },
  onLoad() {
    // 获取用户信息
    this.userInfo = uni.getStorageSync('userInfo');
    if (!this.userInfo) {
      // 如果未登录，跳转到登录页面
      uni.navigateTo({ url: '/pages/teacher/login' });
      return;
    }
    
    // 获取服务器URL
    const savedUrl = uni.getStorageSync('SERVER_URL');
    if (savedUrl) {
      this.SERVER_URL = savedUrl;
    }
    
    // 加载学生列表
    this.queryStudents();
    
    // 加载报警数量
    this.loadAlertCount();
    
    // 监听报警页面的事件
    uni.$on('refreshAlerts', () => {
      this.loadAlertCount();
    });
    
    // 监听从报警页面查看学生在地图上的位置
    uni.$on('showStudentOnMap', (data) => {
      if (data && data.student_id) {
        // 切换到地图视图
        this.activeView = 'map';
        // 延迟执行，确保地图已经渲染
        this.$nextTick(() => {
          // 设置地图中心点为该学生位置
          if (data.latitude && data.longitude) {
            this.mainMapCenter = {
              latitude: parseFloat(data.latitude),
              longitude: parseFloat(data.longitude)
            };
            // 使用地图API移动到指定位置
            setTimeout(() => {
              const mapContext = uni.createMapContext('mainMap', this);
              if (mapContext) {
                mapContext.moveToLocation({
                  latitude: parseFloat(data.latitude),
                  longitude: parseFloat(data.longitude)
                });
              }
            }, 300);
          }
          // 高亮显示该学生
          const student = this.students.find(s => s.student_id === data.student_id);
          if (student) {
            this.selectedStudent = student;
          }
        });
      }
    });
    
    // 监听从报警页面查看学生历史轨迹
    uni.$on('viewStudentHistory', (student) => {
      if (student && student.student_id) {
        // 查找完整的学生信息
        const fullStudent = this.students.find(s => s.student_id === student.student_id);
        if (fullStudent) {
          this.viewStudentHistory(fullStudent);
        } else {
          // 如果本地没有该学生信息，使用传入的信息
          this.viewStudentHistory(student);
        }
      }
    });
  },
  onUnload() {
    // 移除事件监听
    uni.$off('refreshAlerts');
    uni.$off('showStudentOnMap');
    uni.$off('viewStudentHistory');
    // 停止报警闪烁
    this.stopAlertBlink();
  },
  watch: {
    viewMode(newMode) {
      if (newMode === 'map') {
        this.initMap();
      }
    },
    locationHistory() {
      if (this.viewMode === 'map') {
        this.initMap();
      }
    }
  },
  methods: {
    // 加载报警数量
    loadAlertCount() {
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
          if (res.data.code === 200) {
            const alerts = res.data.data;
            this.alertCount = alerts.length;
            
            // 检查是否有新的报警
            if (alerts.length > 0) {
              const hasNewAlerts = alerts.some(alert => {
                if (!this.lastAlertCheckTime) return true;
                // 解析报警时间字符串
                const alertTimeStr = alert.timestamp;
                const alertTime = new Date(alertTimeStr).getTime();
                return alertTime > this.lastAlertCheckTime;
              });
              
              // 如果有新的报警，启动闪烁效果
              if (hasNewAlerts) {
                this.startAlertBlink();
              } else {
                this.stopAlertBlink();
              }
            } else {
              this.stopAlertBlink();
            }
          }
        },
        fail: (err) => {
          console.error('加载报警数量失败:', err);
        }
      });
    },
    
    // 启动报警闪烁
    startAlertBlink() {
      // 如果已经在闪烁，不重复启动
      if (this.alertBlinkTimer) return;
      
      this.alertBlinkTimer = setInterval(() => {
        this.isAlertBlinking = !this.isAlertBlinking;
      }, 500); // 每500ms切换一次状态
    },
    
    // 停止报警闪烁
    stopAlertBlink() {
      if (this.alertBlinkTimer) {
        clearInterval(this.alertBlinkTimer);
        this.alertBlinkTimer = null;
      }
      this.isAlertBlinking = false;
    },
    
    // 跳转到报警页面
    goToAlerts() {
      // 记录查看报警的时间
      this.lastAlertCheckTime = Date.now();
      // 停止闪烁
      this.stopAlertBlink();
      
      uni.navigateTo({
        url: '/pages/teacher/alerts'
      });
    },
    
    // 查询学生列表
    queryStudents() {
      uni.showLoading({ title: '加载中...' });
      
      // 发送查询请求
      uni.request({
        url: `${this.SERVER_URL}/api/get_students`,
        method: 'POST',
        data: {
          grade: this.filter.grade,
          department: this.filter.department,
          major: this.filter.major,
          student_id: this.filter.studentId
        },
        header: {
          'Content-Type': 'application/json'
        },
        success: (res) => {
          uni.hideLoading();
          
          if (res.data.code === 200) {
            this.students = res.data.data;
            // 更新地图标记
            this.updateMapMarkers();
          } else {
            uni.showToast({ title: res.data.msg || '获取学生列表失败', icon: 'none' });
          }
        },
        fail: (err) => {
          uni.hideLoading();
          console.error('获取学生列表失败:', err);
          uni.showToast({ title: '网络错误，请稍后重试', icon: 'none' });
        }
      });
    },
    
    // 刷新学生列表
    refreshStudents() {
      this.queryStudents();
      uni.showToast({ title: '刷新成功', icon: 'success' });
    },
    
    // 查看学生位置历史
    viewStudentHistory(student) {
      this.currentStudent = student;
      this.showHistoryModal = true;
      
      // 获取学生位置历史
      uni.showLoading({ title: '加载历史位置...' });
      
      uni.request({
        url: `${this.SERVER_URL}/api/get_student_locations`,
        method: 'GET',
        data: {
          student_id: student.student_id
        },
        header: {
          'Content-Type': 'application/json'
        },
        success: (res) => {
          uni.hideLoading();
          
          if (res.data.code === 200) {
            // 保存原始数据
            this.originalLocationHistory = res.data.data.location_records;
            // 应用时间筛选
            this.applyTimeFilter();
          } else {
            uni.showToast({ title: res.data.msg || '获取历史位置失败', icon: 'none' });
          }
        },
        fail: (err) => {
          uni.hideLoading();
          console.error('获取历史位置失败:', err);
          uni.showToast({ title: '网络错误，请稍后重试', icon: 'none' });
        }
      });
    },
    
    // 关闭历史位置弹窗
    closeHistoryModal() {
      this.showHistoryModal = false;
      this.currentStudent = {};
      this.locationHistory = [];
      this.originalLocationHistory = [];
      this.viewMode = 'list';
      this.timeFilterIndex = 0;
      
      // 延迟清空地图数据，等待弹窗关闭动画完成
      setTimeout(() => {
        this.markers = [];
        this.polyline = [];
        this.mapCenter = {
          latitude: 33.0105,
          longitude: 114.0065
        };
      }, 300);
    },

    // 时间筛选变化处理
    onTimeFilterChange(e) {
      this.timeFilterIndex = e.detail.value;
      this.applyTimeFilter();
    },

    // 应用时间筛选
    applyTimeFilter() {
      if (!this.originalLocationHistory || this.originalLocationHistory.length === 0) {
        this.locationHistory = [];
        return;
      }

      const now = new Date();
      let cutoffTime = null;

      switch (this.timeFilterIndex) {
        case 1: // 最近1小时
          cutoffTime = new Date(now.getTime() - 60 * 60 * 1000);
          break;
        case 2: // 最近3小时
          cutoffTime = new Date(now.getTime() - 3 * 60 * 60 * 1000);
          break;
        case 3: // 最近6小时
          cutoffTime = new Date(now.getTime() - 6 * 60 * 60 * 1000);
          break;
        case 4: // 最近12小时
          cutoffTime = new Date(now.getTime() - 12 * 60 * 60 * 1000);
          break;
        case 5: // 最近1天
          cutoffTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
          break;
        case 6: // 最近3天
          cutoffTime = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
          break;
        case 7: // 最近7天
          cutoffTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          break;
        default: // 全部
          this.locationHistory = [...this.originalLocationHistory];
          return;
      }

      // 筛选数据
      this.locationHistory = this.originalLocationHistory.filter(record => {
        const recordTime = new Date(record.timestamp);
        return recordTime >= cutoffTime;
      });
    },
    
    // 初始化地图
    initMap() {
      if (this.viewMode === 'map' && this.locationHistory.length > 0) {
        // 准备轨迹点数据
        const points = this.locationHistory.map(record => ({
          latitude: parseFloat(record.latitude),
          longitude: parseFloat(record.longitude),
          timestamp: record.timestamp
        }));
        
        if (points.length > 0) {
          // 设置地图中心点为第一个点
          this.mapCenter = {
            latitude: points[0].latitude,
            longitude: points[0].longitude
          };
          
          // 绘制渐变色轨迹线（从浅蓝到深蓝）
          this.polyline = this.createGradientPolyline(points);
          
          // 添加标记点（使用默认标记，移除图标文件依赖）
          this.markers = points.map((point, index) => {
            // 计算方向角度（如果不是第一个点）
            let rotate = 0;
            if (index > 0) {
              const prevPoint = points[index - 1];
              rotate = this.calculateBearing(prevPoint, point);
            }
            
            return {
              id: index,
              latitude: point.latitude,
              longitude: point.longitude,
              title: point.timestamp,
              // 使用默认标记样式
              iconPath: '', // 空字符串表示使用默认标记
              width: 20,
              height: 20,
              rotate: rotate,
              anchor: {x: 0.5, y: 0.5},
              // 根据位置设置不同的颜色
              color: index === 0 ? '#34a853' : (index === points.length - 1 ? '#ea4335' : '#1a73e8')
            };
          });
        }
      }
    },
    
    // 计算两个点之间的方向角度
    calculateBearing(start, end) {
      const startLat = start.latitude * Math.PI / 180;
      const startLng = start.longitude * Math.PI / 180;
      const endLat = end.latitude * Math.PI / 180;
      const endLng = end.longitude * Math.PI / 180;
      
      const dLng = endLng - startLng;
      const y = Math.sin(dLng) * Math.cos(endLat);
      const x = Math.cos(startLat) * Math.sin(endLat) - Math.sin(startLat) * Math.cos(endLat) * Math.cos(dLng);
      let bearing = Math.atan2(y, x) * 180 / Math.PI;
      
      // 调整为0-360度
      if (bearing < 0) {
        bearing += 360;
      }
      
      return bearing;
    },
    
    // 创建渐变色轨迹线（从浅蓝到深蓝）
    createGradientPolyline(points) {
      if (points.length < 2) return [];
      
      const polylines = [];
      const totalSegments = points.length - 1;
      
      // 浅蓝色到深蓝色的渐变
      // 浅蓝: #87CEEB (135, 206, 235)
      // 深蓝: #00008B (0, 0, 139)
      const startColor = { r: 135, g: 206, b: 235 };
      const endColor = { r: 0, g: 0, b: 139 };
      
      for (let i = 0; i < totalSegments; i++) {
        // 计算当前段的颜色（根据进度插值）
        const progress = i / (totalSegments - 1);
        const r = Math.round(startColor.r + (endColor.r - startColor.r) * progress);
        const g = Math.round(startColor.g + (endColor.g - startColor.g) * progress);
        const b = Math.round(startColor.b + (endColor.b - startColor.b) * progress);
        const color = `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
        
        polylines.push({
          points: [
            { latitude: points[i].latitude, longitude: points[i].longitude },
            { latitude: points[i + 1].latitude, longitude: points[i + 1].longitude }
          ],
          color: color,
          width: 4,
          dottedLine: false
        });
      }
      
      return polylines;
    },
    
    // 更新地图标记
    updateMapMarkers() {
      const markers = [];
      
      this.students.forEach((student, index) => {
        const location = student.location;
        if (location && location.latitude && location.longitude) {
          // 为每个学生分配一个颜色
          const colorIndex = index % this.studentColors.length;
          const color = this.studentColors[colorIndex];
          
          // 获取学号后三位
          const studentId = student.student_id;
          const studentIdSuffix = studentId.substring(studentId.length - 3);
          
          // 创建标记
          markers.push({
            id: student.student_id,
            latitude: parseFloat(location.latitude),
            longitude: parseFloat(location.longitude),
            title: `${student.name} (${studentId})`,
            // 使用默认标记，通过color属性设置颜色
            iconPath: '',
            width: 30,
            height: 40,
            anchor: { x: 0.5, y: 1 },
            color: color,
            // 显示学号后三位
            label: {
              content: studentIdSuffix,
              color: '#fff',
              fontSize: 12,
              fontWeight: 'bold',
              x: 0,
              y: -10
            }
          });
        }
      });
      
      this.mainMapMarkers = markers;
      this.mainMapPolylines = []; // 清空轨迹线
    },

    // 点击地图标记
    onMarkerTap(e) {
      const markerId = e.detail.markerId;
      // 根据学号查找学生
      const student = this.students.find(s => s.student_id === markerId);
      if (student) {
        this.selectedStudent = student;
      }
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

.welcome {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.teacher-id, .student-id {
  font-size: 14px;
  color: #666;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.alert-btn {
  position: relative;
  padding: 8px 15px;
  background-color: #ea4335;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.alert-btn.blink {
  background-color: #ff0000;
  box-shadow: 0 0 15px rgba(255, 0, 0, 0.8);
  transform: scale(1.05);
}

.alert-text {
  color: #fff;
}

.alert-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background-color: #fff;
  color: #ea4335;
  font-size: 10px;
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 10px;
  border: 1px solid #ea4335;
}

.refresh-btn {
  padding: 8px 15px;
  background-color: #1a73e8;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 14px;
}

.refresh-text {
  color: #fff;
}

.filter-section {
  margin-bottom: 10px;
  padding: 10px 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.filter-row {
  display: flex;
  margin-bottom: 15px;
  gap: 15px;
}

.filter-item {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.filter-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.filter-input {
  height: 40px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0 10px;
  font-size: 14px;
}

.filter-btn {
  width: 100%;
  height: 40px;
  background-color: #1a73e8;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
}

.view-tabs {
  display: flex;
  margin-bottom: 10px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #ddd;
}

.tab-btn {
  flex: 1;
  padding: 10px;
  border: none;
  background-color: #f5f5f5;
  font-size: 16px;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.tab-btn.active {
  background-color: #1a73e8;
  color: #fff;
}

.map-section {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  height: 500px;
}

.student-section {
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.section-title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  margin-bottom: 15px;
}

.student-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.student-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.student-item:hover {
  background-color: #f0f0f0;
}

.student-info {
  flex: 1;
}

.student-name {
  display: block;
  font-size: 16px;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.student-detail {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 5px;
}

.student-detail text {
  font-size: 12px;
  color: #666;
}

.separator {
  color: #999;
}

.student-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.location-status {
  padding: 4px 10px;
  border-radius: 15px;
  font-size: 12px;
  font-weight: bold;
  color: #fff;
  white-space: nowrap;
}

.speed-info {
  font-size: 11px;
  font-weight: bold;
  white-space: nowrap;
  padding: 2px 8px;
  border-radius: 12px;
  background-color: #f5f5f5;
  margin-top: 2px;
}

.in-campus {
  background-color: #34a853;
}

.out-campus {
  background-color: #ea4335;
}

.update-time {
  font-size: 12px;
  color: #999;
}

.empty-tip {
  text-align: center;
  padding: 30px;
  color: #999;
  font-size: 14px;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
}

.modal-content {
  width: 90%;
  max-height: 80%;
  background-color: #fff;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #eee;
}

.modal-title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.modal-header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.time-filter {
  margin-right: 10px;
}

.picker-view {
  display: flex;
  align-items: center;
  padding: 5px 10px;
  background-color: #f5f5f5;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.picker-text {
  font-size: 14px;
  color: #333;
  margin-right: 5px;
}

.picker-arrow {
  font-size: 10px;
  color: #666;
}

.view-toggle {
  display: flex;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #ddd;
}

.toggle-btn {
  padding: 5px 10px;
  border: none;
  background-color: #f5f5f5;
  font-size: 14px;
  color: #666;
  cursor: pointer;
}

.toggle-btn.active {
  background-color: #1a73e8;
  color: #fff;
}

.modal-close {
  font-size: 24px;
  color: #999;
  cursor: pointer;
}

.map-container {
  width: 100%;
  height: 100%;
}

.map-container.full-height {
  position: relative;
  height: calc(100vh - 200px);
}

.map {
  width: 100%;
  height: 100%;
  border-radius: 8px;
}

.map.map-expand {
  border-radius: 8px;
  height: calc(100vh - 320px);
  min-height: 400px;
}

/* 地图全屏样式 */
.map-section.map-fullscreen {
  margin-bottom: 10px;
  padding: 10px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  flex: 1;
  display: flex;
  flex-direction: column;
}

.map-wrapper {
  position: relative;
  width: 100%;
}

/* 学生信息卡片 */
.student-info-card {
  margin-top: 15px;
  background-color: #fff;
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.card-title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.card-close {
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0 5px;
}

.card-body {
  margin-bottom: 15px;
}

.info-row {
  display: flex;
  margin-bottom: 8px;
  align-items: center;
}

.info-label {
  font-size: 14px;
  color: #666;
  width: 80px;
  flex-shrink: 0;
}

.info-value {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.card-footer {
  display: flex;
  justify-content: center;
}

.view-history-btn {
  background-color: #1a73e8;
  color: #fff;
  border: none;
  border-radius: 20px;
  padding: 10px 30px;
  font-size: 14px;
  cursor: pointer;
}

.modal-body {
  padding: 15px;
  overflow-y: auto;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.history-item {
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.history-time {
  font-size: 14px;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.history-location {
  margin-bottom: 5px;
}

.location-coord {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 3px;
}

.location-address {
  display: block;
  font-size: 12px;
  color: #999;
  word-break: break-all;
}

.history-status {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  color: #fff;
}

/* 历史记录信息区域 */
.history-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 5px;
}

/* 历史记录速度信息 */
.history-speed {
  font-size: 11px;
  font-weight: bold;
}
/* 速度信息样式 */
.speed-info {
  font-size: 12px;
  margin-left: 5px;
  font-weight: bold;
}

/* 列表视图中的速度信息 */
.student-status .speed-info {
  font-size: 11px;
  margin-left: 3px;
}

/* 超速样式 */
.speed-over {
  color: #ea4335 !important;
}

/* 正常速度样式 */
.speed-normal {
  color: #34a853 !important;
}

/* 状态文字样式 */
.location-status {
  display: flex;
  align-items: center;
  gap: 5px;
}
</style>