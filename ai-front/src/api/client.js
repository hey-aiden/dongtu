import axios from 'axios';

// 后端服务地址。dev 下经 CORS 直连;后续改走代理或上环境变量,只需改这一处。
const BASE_URL = 'http://localhost:8000/dongtu';

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // LLM 回复可能触发滚动摘要,耗时较长
  headers: { 'Content-Type': 'application/json' },
});

// 响应拦截器:统一解包 data + 归一化错误信息,调用方拿到即业务数据或统一 Error
client.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const detail = err.response?.data?.detail;
    const message =
      typeof detail === 'string'
        ? detail
        : detail
          ? JSON.stringify(detail)
          : err.code === 'ECONNABORTED'
            ? '请求超时,请重试'
            : err.message || '请求失败,请稍后重试';
    return Promise.reject(new Error(message));
  },
);

export default client;
