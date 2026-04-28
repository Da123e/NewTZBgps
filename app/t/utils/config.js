// 全局配置文件
export const config = {
  // 服务器配置
  SERVER_URL: "http://10.179.122.40:8000",
  
  // API路径配置
  API: {
    LOGIN: "/api/login",
    REGISTER: "/api/register",
    GET_LOCATION: "/api/location",
    UPLOAD_LOCATION: "/api/location/upload",
    GET_ALERTS: "/api/alerts"
  },
  
  // 存储键名
  STORAGE_KEYS: {
    USER_INFO: 'userInfo',
    SERVER_URL: 'SERVER_URL'
  }
};

// 导出默认配置
export default config;