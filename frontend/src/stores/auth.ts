import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from '@/api/http'

interface User {
  id: string | number
  username: string
  full_name: string
  role: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const res = await axios.post('/auth/login', { username, password })
    token.value = res.data.token
    user.value = {
      id: res.data.user_id,
      username: res.data.username,
      full_name: res.data.full_name,
      role: res.data.role,
    }
    localStorage.setItem('token', token.value)
    localStorage.setItem('user', JSON.stringify(user.value))
    return res.data
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isLoggedIn, login, logout }
})
