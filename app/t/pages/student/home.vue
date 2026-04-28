<template>
  <view class="container">
    <!-- 头部信息 -->
    <view class="header">
      <text class="welcome">欢迎，{{ userInfo.name }}</text>
      <text class="student-id">学号：{{ userInfo.student_id }}</text>
      <text class="student-class">班级：{{ userInfo.class_name || '未设置' }}</text>
    </view>
    
    <!-- 位置信息 -->
    <view class="location-section">
      <view class="location-info">
        <view class="info-item">
          <text class="label">纬度：</text>
          <text class="value">{{ latitude || '---' }}</text>
        </view>
        <view class="info-item">
          <text class="label">经度：</text>
          <text class="value">{{ longitude || '---' }}</text>
        </view>
        <view class="info-item">
          <text class="label">地址：</text>
          <text class="value address">{{ address || '获取中...' }}</text>
        </view>
        <view class="info-item">
          <text class="label">状态：</text>
          <text class="value" :class="{'in-campus': isOnCampus === true, 'out-campus': isOnCampus === false}">
            {{ campusStatus }}
          </text>
        </view>
        <view class="info-item">
          <text class="label">速度：</text>
          <text class="value" :class="{'speed-over': speed >= 35.76, 'speed-normal': speed && speed < 35.76}">
            {{ speed !== null && speed !== undefined ? speed.toFixed(2) + ' m/s' : '---' }}
          </text>
        </view>
      </view>
    </view>
    
    <!-- 控制按钮 -->
    <view class="btn-section">
      <button 
        class="btn" 
        :class="gpsRunning ? 'stop-btn' : 'start-btn'" 
        @click="toggleGps"
      >
        {{ gpsRunning ? '停止定位' : '开始定位' }}
      </button>
      <button 
        class="btn upload-btn" 
        @click="manualUpload"
        :disabled="!gpsRunning || !latitude || !longitude"
        style="margin-top: 10px;"
      >
        手动上传位置
      </button>
    </view>
    
    <!-- 状态提示 -->
    <view class="status-section">
      <text class="status-text">{{ statusText }}</text>
    </view>
  </view>
</template>

<script>
import config from '../../utils/config.js';

// 扩展Math对象，添加角度转弧度的方法
Math.radians = function(degrees) {
  return degrees * Math.PI / 180;
};

// WGS84坐标系转GCJ-02坐标系（火星坐标系）
function wgs84ToGcj02(lng, lat) {
  const PI = 3.1415926535897932384626;
  const a = 6378245.0;
  const ee = 0.00669342162296594323;

  let dlat = transformLat(lng - 105.0, lat - 35.0);
  let dlng = transformLng(lng - 105.0, lat - 35.0);
  const radlat = lat / 180.0 * PI;
  let magic = Math.sin(radlat);
  magic = 1 - ee * magic * magic;
  const sqrtmagic = Math.sqrt(magic);
  dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * PI);
  dlng = (dlng * 180.0) / (a / sqrtmagic * Math.cos(radlat) * PI);
  const mglat = lat + dlat;
  const mglng = lng + dlng;
  return [mglng, mglat];
}

function transformLat(lng, lat) {
  const PI = 3.1415926535897932384626;
  let ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * Math.sqrt(Math.abs(lng));
  ret += (20.0 * Math.sin(6.0 * lng * PI) + 20.0 * Math.sin(2.0 * lng * PI)) * 2.0 / 3.0;
  ret += (20.0 * Math.sin(lat * PI) + 40.0 * Math.sin(lat / 3.0 * PI)) * 2.0 / 3.0;
  ret += (160.0 * Math.sin(lat / 12.0 * PI) + 320 * Math.sin(lat * PI / 30.0)) * 2.0 / 3.0;
  return ret;
}

function transformLng(lng, lat) {
  const PI = 3.1415926535897932384626;
  let ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * Math.sqrt(Math.abs(lng));
  ret += (20.0 * Math.sin(6.0 * lng * PI) + 20.0 * Math.sin(2.0 * lng * PI)) * 2.0 / 3.0;
  ret += (20.0 * Math.sin(lng * PI) + 40.0 * Math.sin(lng / 3.0 * PI)) * 2.0 / 3.0;
  ret += (150.0 * Math.sin(lng / 12.0 * PI) + 300.0 * Math.sin(lng / 30.0 * PI)) * 2.0 / 3.0;
  return ret;
}

// 黄淮学院北区边界坐标（用户提供的新坐标）
const HUANGHUAI_COLLEGE_NORTH_POLYGON = [
  [114.00760883217328, 33.01498104364417],
  [114.00954423394002, 33.015026928694994],
  [114.01139885612503, 33.009468648207346],
  [114.00341637439402, 33.007172907558214],
  [114.00281526152678, 33.01302517042209],
  [114.00760883217328, 33.01498104364417]
];

// 射线法判断点是否在多边形内
function isPointInPolygon(pointLon, pointLat, polygon) {
  let inside = false;
  const n = polygon.length;
  
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    
    if ((polygon[i][1] > pointLat) !== (polygon[j][1] > pointLat)) {
      const intersectLon = ((polygon[j][0] - polygon[i][0]) * (pointLat - polygon[i][1]) / 
                         (polygon[j][1] - polygon[i][1]) + polygon[i][0]);
      
      if (pointLon < intersectLon) {
        inside = !inside;
      }
    }
  }
  
  return inside;
}

// 定位容错半径（米）- 用于处理GPS定位误差
const LOCATION_TOLERANCE = 100; // 与服务器端保持一致

// 计算两点之间的距离（米）- 使用Haversine公式
function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371000; // 地球半径（米）
  const lat1_rad = Math.radians(lat1);
  const lat2_rad = Math.radians(lat2);
  const delta_lat = Math.radians(lat2 - lat1);
  const delta_lon = Math.radians(lon2 - lon1);
  
  const a = Math.sin(delta_lat / 2) ** 2 + 
            Math.cos(lat1_rad) * Math.cos(lat2_rad) * Math.sin(delta_lon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  
  return R * c;
}

// 计算点到线段的距离
function pointToSegmentDistance(lat, lon, lat1, lon1, lat2, lon2) {
  // 将经纬度转换为米（近似）
  const lat_avg = (lat1 + lat2) / 2;
  const meters_per_deg_lat = 111000;
  const meters_per_deg_lon = 111000 * Math.cos(Math.radians(lat_avg));
  
  // 转换为米坐标
  const px_m = lon * meters_per_deg_lon;
  const py_m = lat * meters_per_deg_lat;
  const x1_m = lon1 * meters_per_deg_lon;
  const y1_m = lat1 * meters_per_deg_lat;
  const x2_m = lon2 * meters_per_deg_lon;
  const y2_m = lat2 * meters_per_deg_lat;
  
  // 计算点到线段的距离
  const dx = x2_m - x1_m;
  const dy = y2_m - y1_m;
  
  if (dx === 0 && dy === 0) {
    return Math.sqrt((px_m - x1_m) ** 2 + (py_m - y1_m) ** 2);
  }
  
  const t = Math.max(0, Math.min(1, ((px_m - x1_m) * dx + (py_m - y1_m) * dy) / (dx ** 2 + dy ** 2)));
  
  const closest_x = x1_m + t * dx;
  const closest_y = y1_m + t * dy;
  
  return Math.sqrt((px_m - closest_x) ** 2 + (py_m - closest_y) ** 2);
}

// 计算点到多边形边界的最短距离
function distanceToPolygon(latitude, longitude, polygon) {
  let min_distance = Infinity;
  const n = polygon.length;
  
  // 遍历多边形的每条边，包括最后一条边（从最后一个点到第一个点）
  for (let i = 0; i < n; i++) {
    const [lon1, lat1] = polygon[i];
    const [lon2, lat2] = polygon[(i + 1) % n]; // 使用模运算确保闭合
    
    // 计算点到线段的距离
    const distance = pointToSegmentDistance(latitude, longitude, lat1, lon1, lat2, lon2);
    min_distance = Math.min(min_distance, distance);
  }
  
  return min_distance;
}

// 判断是否在校内（带容错机制）
function isOnCampus(latitude, longitude, accuracy = 0) {
  // 首先检查点是否在多边形内
  const inside_polygon = isPointInPolygon(longitude, latitude, HUANGHUAI_COLLEGE_NORTH_POLYGON);
  
  if (inside_polygon) {
    return true;
  }
  
  // 如果不在多边形内，检查是否在容错范围内
  // 计算点到多边形边界的距离
  const distance_to_boundary = distanceToPolygon(latitude, longitude, HUANGHUAI_COLLEGE_NORTH_POLYGON);
  
  // 使用定位精度和容错半径中的较大值
  const tolerance = Math.max(accuracy, LOCATION_TOLERANCE);
  
  // 如果在容错范围内，认为在校内
  return distance_to_boundary <= tolerance;
}

export default {
  data() {
    return {
      // 用户信息
      userInfo: {},
      // 服务器配置
      SERVER_URL: config.SERVER_URL,
      // 定位状态
      gpsRunning: false,
      // 上传间隔（秒）
      uploadInterval: 60, // 默认60秒
      // 定时任务ID
      uploadTimer: null,
      // 定位监听器ID（用于停止定位）
      locationWatcher: null,
      // UI显示数据
      statusText: "未开始定位",
      latitude: null,
      longitude: null,
      accuracy: 0,
      speed: null,
      address: "获取中...",
      // 是否在校内
      isOnCampus: null,
      campusStatus: "未知"
    };
  },
  onLoad() {
    // 获取用户信息
    this.userInfo = uni.getStorageSync('userInfo');
    if (!this.userInfo) {
      // 如果未登录，跳转到登录页面
      uni.navigateTo({ url: '/pages/student/login' });
      return;
    }
    
    // 获取服务器URL
    const savedUrl = uni.getStorageSync('SERVER_URL');
    if (savedUrl) {
      this.SERVER_URL = savedUrl;
    }
    
    // 检查安卓定位权限
    this.checkAndroidPermissions();
  },
  onUnload() {
    // 页面卸载时停止定位和上传
    this.stopGps();
  },
  methods: {
    // 检查安卓定位权限（仅APP端）
    checkAndroidPermissions() {
      // #ifdef APP-PLUS
      plus.android.requestPermissions(
        ["android.permission.ACCESS_FINE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION"],
        (result) => {
          const granted = result.filter(item => item.granted).length === 2;
          if (!granted) {
            uni.showModal({
              title: "权限不足",
              content: "请授予定位权限，否则无法使用定位功能",
              showCancel: false
            });
          }
        },
        (err) => {
          console.error("请求权限失败：", err);
        }
      );
      // #endif
    },
    
    // 切换GPS开关
    toggleGps() {
      if (this.gpsRunning) {
        this.stopGps();
      } else {
        this.startGps();
      }
    },
    
    // 手动上传位置
    manualUpload() {
      this.uploadLocation(true);
    },
    
    // 开始定位
    startGps() {
      try {
        // 重置状态
        this.address = "获取中...";
        this.statusText = "定位中...";
        this.isOnCampus = null;
        this.campusStatus = "未知";
        
        // #ifdef APP-PLUS
        // APP端使用plus.geolocation（原生，更稳定）
        this.locationWatcher = plus.geolocation.watchPosition(
          (position) => {
            this.onLocationSuccess(position);
          },
          (error) => {
            this.statusText = `定位失败: ${error.message}`;
            this.address = "定位失败";
          },
          {
            enableHighAccuracy: true, // 高精度模式
            maximumAge: 500, // 最大缓存时间，降低为500ms
            timeout: 3000, // 超时时间，降低为3秒
            provider: "system",
            coordsType: "wgs84" // 使用WGS84坐标系（APP端plus.geolocation不支持gcj02）
          }
        );
        // #endif
        
        // #ifndef APP-PLUS
        // H5/小程序使用uni.getLocation（原生接口）
        uni.getLocation({
          type: "gcj02",
          geocode: true, // 开启逆地理编码（自动解析地址）
          success: (res) => {
            this.onLocationSuccess(res);
            // 定时获取位置（H5/小程序需要自己实现定时）
            this.locationWatcher = setInterval(() => {
              uni.getLocation({
                type: "gcj02",
                geocode: true,
                success: (res) => {
                  this.onLocationSuccess(res);
                },
                fail: (err) => {
                  console.error('定位失败:', err);
                }
              });
            }, 5000); // 每5秒获取一次位置
          },
          fail: (err) => {
            this.statusText = `定位失败: ${err.errMsg}`;
            this.address = "定位失败";
          }
        });
        // #endif
        
        // 更新定位状态
        this.gpsRunning = true;
        
        // 启动定时自动上传（初始延迟1秒）
        setTimeout(() => {
          this.uploadTimer = setInterval(() => {
            this.uploadLocation(false);
          }, this.uploadInterval * 1000);
          // 立即上传一次
          this.uploadLocation(false);
        }, 1000);
        
      } catch (e) {
        this.statusText = `启动失败: ${e.message}`;
        this.address = "启动失败";
      }
    },
    
    // 停止定位
    stopGps() {
      try {
        // 停止GPS监听
        if (this.locationWatcher) {
          // #ifdef APP-PLUS
          plus.geolocation.clearWatch(this.locationWatcher);
          // #endif
          
          // #ifndef APP-PLUS
          clearInterval(this.locationWatcher);
          // #endif
          
          this.locationWatcher = null;
        }
        
        // 停止定时上传
        if (this.uploadTimer) {
          clearInterval(this.uploadTimer);
          this.uploadTimer = null;
        }
        
        // 重置所有状态
        this.gpsRunning = false;
        this.statusText = "已停止定位";
        this.latitude = null;
        this.longitude = null;
        this.accuracy = 0;
        this.speed = null;
        this.address = "";
        this.isOnCampus = null;
        this.campusStatus = "未知";
        
      } catch (e) {
        this.statusText = `停止失败: ${e.message}`;
      }
    },
    
    // 定位成功统一处理（兼容多端返回格式）
    onLocationSuccess(position) {
      try {
        // 调试：打印完整的position对象
        console.log('[DEBUG] 定位返回数据:', JSON.stringify(position));
        console.log('[DEBUG] position.coords:', position.coords);
        console.log('[DEBUG] position.speed:', position.speed);
        
        // 提取核心定位数据（兼容plus和uni接口）
        let latitude = position.coords?.latitude || position.latitude;
        let longitude = position.coords?.longitude || position.longitude;
        this.accuracy = position.coords?.accuracy || position.accuracy || 0;
        this.speed = position.coords?.speed !== undefined ? position.coords.speed : (position.speed !== undefined ? position.speed : null);
        
        // #ifdef APP-PLUS
        // APP端使用plus.geolocation返回的是WGS84坐标，需要转换为GCJ-02
        const converted = wgs84ToGcj02(longitude, latitude);
        longitude = converted[0];
        latitude = converted[1];
        console.log('[DEBUG] WGS84转GCJ-02:', longitude, latitude);
        // #endif
        
        this.latitude = latitude;
        this.longitude = longitude;
        
        console.log('[DEBUG] 提取的速度:', this.speed);
        
        // 解析地址（原生方式，无需第三方API）
        this.parseAddress(position);
        
        // 本地判断校内/校外状态
        const campusStatus = isOnCampus(this.latitude, this.longitude, this.accuracy);
        this.isOnCampus = campusStatus;
        this.campusStatus = campusStatus ? "校内" : "校外";
        
        // 更新状态
        this.statusText = "定位中...";
        
      } catch (e) {
        this.statusText = `位置解析失败: ${e.message}`;
        this.address = "解析失败";
      }
    },
    
    // 原生解析地址（多端兼容）
    parseAddress(position) {
      // #ifdef APP-PLUS
      // APP端直接从定位结果取地址
      if (position.address) {
        this.address = position.address.province + position.address.city + 
                       position.address.district + position.address.street;
      } else {
        // 兜底：APP端无地址时用坐标拼接
        this.address = `(${this.latitude.toFixed(6)}, ${this.longitude.toFixed(6)})`;
      }
      // #endif
      
      // #ifndef APP-PLUS
      // H5/小程序：uni.getLocation开启geocode后，res包含address
      if (position.address) {
        this.address = position.address;
      } else {
        this.address = `(${this.latitude.toFixed(6)}, ${this.longitude.toFixed(6)})`;
      }
      // #endif
    },
    
    // 通用上传方法（区分自动/手动）
    uploadLocation(isManual) {
      if (!this.latitude || !this.longitude) {
        const tip = isManual ? "暂无位置数据，无法上传" : "暂无位置数据，跳过上传";
        this.statusText = tip;
        if (isManual) {
          uni.showToast({ title: tip, icon: 'none' });
        }
        return;
      }
      
      try {
        // 重新获取用户信息，确保最新
        this.userInfo = uni.getStorageSync('userInfo');
        
        // 调试：打印用户信息
        console.log('[DEBUG] 用户信息:', this.userInfo);
        // 构造上传数据
        const data = {
          student_id: this.userInfo.student_id || '',
          device_id: this.userInfo.device_id || '',
          latitude: Number(this.latitude),
          longitude: Number(this.longitude),
          accuracy: Number(this.accuracy),
          speed: this.speed !== null && this.speed !== undefined ? Number(this.speed) : null,
          address: this.address
        };
        
        // 调试：打印上传数据
        console.log('[DEBUG] 上传数据:', data);
        
        // 发送POST请求
        uni.request({
          url: `${this.SERVER_URL}/api/upload_location`,
          method: "POST",
          data: data,
          header: {
            "Content-Type": "application/json"
          },
          timeout: 10000,
          success: (res) => {
            const result = res.data;
            const type = isManual ? "手动" : "自动";
            
            if (result?.code === 200) {
              this.statusText = `${type}上传成功`;
              // 更新校内/校外状态
              this.isOnCampus = result.data.is_on_campus;
              this.campusStatus = result.data.is_on_campus ? "校内" : "校外";
              
              // 根据校内/校外状态调整上传间隔
              this.uploadInterval = result.data.is_on_campus ? 180 : 60; // 校内3分钟，校外1分钟
              
              // 如果上传间隔改变，重启定时器
              if (this.uploadTimer && this.gpsRunning) {
                clearInterval(this.uploadTimer);
                this.uploadTimer = setInterval(() => {
                  this.uploadLocation(false);
                }, this.uploadInterval * 1000);
              }
            } else {
              this.statusText = `${type}上传失败: ${result?.msg || '未知错误'}`;
            }
          },
          fail: (err) => {
            const type = isManual ? "手动" : "自动";
            this.statusText = `${type}上传网络错误: ${err.errMsg}`;
            console.error("上传失败详情：", err);
          }
        });
        
      } catch (e) {
        const type = isManual ? "手动" : "自动";
        this.statusText = `${type}上传异常: ${e.message}`;
      }
    }
  }
};
</script>

<style scoped>
.container {
  padding: 20px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.welcome {
  display: block;
  font-size: 18px;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.student-id {
  display: block;
  font-size: 14px;
  color: #666;
}

.student-class {
  display: block;
  font-size: 14px;
  color: #666;
  margin-top: 5px;
}

.location-section {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.location-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  display: flex;
  align-items: center;
}

.label {
  font-size: 14px;
  color: #666;
  width: 60px;
}

.value {
  font-size: 14px;
  color: #333;
  flex: 1;
}

.address {
  word-break: break-all;
}

.in-campus {
  color: #34a853;
  font-weight: bold;
}

.out-campus {
  color: #ea4335;
  font-weight: bold;
}

.speed-normal {
  color: #34a853;
  font-weight: bold;
}

.speed-over {
  color: #ea4335;
  font-weight: bold;
}

.btn-section {
  margin-bottom: 20px;
}

.btn {
  width: 100%;
  height: 48px;
  line-height: 48px;
  font-size: 18px;
  border-radius: 8px;
  border: none;
  color: #fff;
  font-weight: 500;
}

.start-btn {
  background-color: #34a853;
}

.stop-btn {
  background-color: #ea4335;
}

.upload-btn {
  background-color: #1a73e8;
}

.upload-btn:disabled {
  background-color: #cccccc;
}

.status-section {
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
  flex: 1;
}

.status-text {
  font-size: 14px;
  color: #666;
}
</style>