<template>
  <div class="pa-6">
    <h1 class="mb-6">清洁复位管理</h1>

    <v-card>
      <v-card-text>
        <v-tabs v-model="activeTab" color="primary" density="comfortable" class="mb-4">
          <v-tab value="all">全部</v-tab>
          <v-tab value="cleaning">待清洁</v-tab>
          <v-tab value="reset_check">待复位</v-tab>
        </v-tabs>

        <v-data-table
          :headers="headers"
          :items="filteredCarts"
          :items-per-page="10"
          class="elevation-1"
        >
          <template #item.cartType="{ item }">
            {{ cartTypeMap[item.cartType] || item.cartType }}
          </template>
          <template #item.status="{ item }">
            <v-chip :color="statusColorMap[item.status]" size="small">
              {{ statusMap[item.status] || item.status }}
            </v-chip>
          </template>
          <template #item.lastCleanedAt="{ item }">
            {{ item.lastCleanedAt ? formatTime(item.lastCleanedAt) : '-' }}
          </template>
          <template #item.actions="{ item }">
            <v-btn
              v-if="item.status === 'cleaning'"
              color="success"
              size="small"
              variant="flat"
              @click="handleCleanComplete(item)"
            >
              完成清洁
            </v-btn>
            <v-btn
              v-else-if="item.status === 'reset_check'"
              color="primary"
              size="small"
              variant="flat"
              @click="handleResetComplete(item)"
            >
              复位通过投放
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from '@/api/http'
import dayjs from 'dayjs'

interface Cart {
  id?: number
  cartNo: string
  cartType: 'standard' | 'large'
  stationId: number | null
  stationName?: string
  status: 'available' | 'borrowed' | 'stranded' | 'transferring' | 'cleaning' | 'reset_check'
  lastCleanedAt?: string
}

const carts = ref<Cart[]>([])
const activeTab = ref('all')

const statusMap: Record<string, string> = {
  available: '可用',
  borrowed: '借出中',
  stranded: '滞留',
  transferring: '调拨中',
  cleaning: '清洁中',
  reset_check: '复位检查中',
}

const statusColorMap: Record<string, string> = {
  available: 'success',
  borrowed: 'primary',
  stranded: 'error',
  transferring: 'warning',
  cleaning: 'info',
  reset_check: 'warning',
}

const cartTypeMap: Record<string, string> = {
  standard: '标准款',
  large: '大号款',
}

const headers = [
  { title: '推车编号', key: 'cartNo' },
  { title: '车型', key: 'cartType' },
  { title: '所属服务点', key: 'stationName' },
  { title: '当前状态', key: 'status' },
  { title: '最近清洁时间', key: 'lastCleanedAt' },
  { title: '操作', key: 'actions', width: '180px' },
]

const filteredCarts = computed(() => {
  const cleaningAndReset = carts.value.filter(
    (c) => c.status === 'cleaning' || c.status === 'reset_check'
  )
  if (activeTab.value === 'all') {
    return cleaningAndReset
  }
  return cleaningAndReset.filter((c) => c.status === activeTab.value)
})

const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const loadCarts = async () => {
  try {
    const res = await axios.get('/carts')
    carts.value = res.data.data || res.data || []
  } catch (e) {
    alert('加载推车列表失败')
  }
}

const handleCleanComplete = async (cart: Cart) => {
  if (!cart.id) return
  try {
    await axios.post(`/carts/${cart.id}/clean`)
    loadCarts()
  } catch (e) {
    alert('完成清洁操作失败')
  }
}

const handleResetComplete = async (cart: Cart) => {
  if (!cart.id) return
  try {
    await axios.put(`/carts/${cart.id}`, { ...cart, status: 'available' })
    loadCarts()
  } catch (e) {
    alert('复位投放操作失败')
  }
}

onMounted(() => {
  loadCarts()
})
</script>
