<template>
  <v-container class="d-flex align-center justify-center" style="min-height: 100vh;">
    <v-card width="400" class="pa-6">
      <v-card-title class="text-center mb-4">系统登录</v-card-title>
      <v-card-text>
        <v-alert
          v-if="error"
          type="error"
          variant="tonal"
          class="mb-4"
          @click:close="error = ''"
          closable
        >
          {{ error }}
        </v-alert>
        <v-form @submit.prevent="handleLogin">
          <v-text-field
            v-model="form.username"
            label="用户名"
            prepend-icon="mdi-account"
            variant="outlined"
            class="mb-4"
          />
          <v-text-field
            v-model="form.password"
            label="密码"
            type="password"
            prepend-icon="mdi-lock"
            variant="outlined"
            class="mb-6"
          />
          <v-btn
            color="primary"
            block
            :loading="loading"
            size="large"
            type="submit"
          >
            登录
          </v-btn>
        </v-form>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({
  username: '',
  password: '',
})

const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(form.username, form.password)
    router.push('/dashboard')
  } catch (e: any) {
    error.value = e.response?.data?.message || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>
