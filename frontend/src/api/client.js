import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    console.error('[api]', err?.config?.url, err?.message)
    return Promise.reject(err)
  }
)

export default api
