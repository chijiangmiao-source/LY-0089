<template>
  <v-layout>
    <v-navigation-drawer v-model="drawer" app>
      <v-list nav density="comfortable">
        <v-list-item
          v-for="item in menuItems"
          :key="item.to"
          :to="item.to"
          :title="item.title"
        >
          <template #prepend>
            <v-icon :icon="item.icon" size="20" />
          </template>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar app color="primary" dark>
      <v-app-bar-nav-icon @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
      <v-app-bar-title>商场儿童推车管理系统</v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn v-if="auth.user" icon variant="text">
        <v-icon icon="mdi-account-circle" />
      </v-btn>
      <span v-if="auth.user" class="ml-2 mr-4">{{ auth.user.full_name || auth.user.username }}</span>
      <v-btn @click="handleLogout" variant="text">
        <v-icon icon="mdi-logout" start />
        退出
      </v-btn>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const drawer = ref(true)

const menuItems = [
  { title: '调度看板', to: '/dashboard', icon: 'mdi-view-dashboard' },
  { title: '服务点管理', to: '/stations', icon: 'mdi-map-marker' },
  { title: '推车档案', to: '/carts', icon: 'mdi-cart' },
  { title: '借出登记', to: '/borrow', icon: 'mdi-arrow-up-bold-circle' },
  { title: '归还登记', to: '/return', icon: 'mdi-arrow-down-bold-circle' },
  { title: '借还记录', to: '/rentals', icon: 'mdi-history' },
  { title: '滞留上报', to: '/stranded', icon: 'mdi-alert-circle' },
  { title: '跨点调拨', to: '/transfers', icon: 'mdi-swap-horizontal' },
  { title: '清洁复位', to: '/cleaning', icon: 'mdi-spray-bottle' },
]

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
