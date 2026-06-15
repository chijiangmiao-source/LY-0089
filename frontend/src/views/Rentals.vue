<template>
  <div class="pa-6">
    <h1 class="mb-6">借还记录</h1>

    <v-card>
      <v-card-text>
        <v-row class="mb-4">
          <v-col cols="4">
            <v-select
              v-model="stageFilter"
              label="筛选环节"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
              :items="stageOptions"
            />
          </v-col>
          <v-col cols="4">
            <v-text-field
              v-model="searchPhone"
              label="搜索手机号"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="4" class="d-flex justify-end align-end">
            <v-btn color="primary" @click="loadRentals">
              查询
            </v-btn>
          </v-col>
        </v-row>

        <v-data-table
          :headers="headers"
          :items="rentals"
          :items-per-page="10"
          class="elevation-1"
          :loading="loading"
        >
          <template #item.stage="{ item }">
            <v-chip :color="stageColorMap[item.stage]" size="small">
              {{ item.stage_display || stageMap[item.stage] || item.stage }}
            </v-chip>
          </template>
          <template #item.borrow_time="{ item }">
            {{ formatTime(item.borrow_time) }}
          </template>
          <template #item.return_time="{ item }">
            {{ item.return_time ? formatTime(item.return_time) : '-' }}
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from '@/api/http'
import dayjs from 'dayjs'

interface Rental {
  id: number
  rental_no: string
  user_phone: string
  borrow_time: string
  return_time: string | null
  borrow_station_id: number
  borrow_station_name: string
  return_station_id: number | null
  return_station_name: string | null
  cart_id: number
  cart_no: string
  stage: string
  stage_display: string
}

const rentals = ref<Rental[]>([])
const stageFilter = ref<string | null>(null)
const searchPhone = ref('')
const loading = ref(false)

const stageMap: Record<string, string> = {
  borrowing: '借用中',
  returned: '已归还',
  overdue: '逾期未还',
}

const stageColorMap: Record<string, string> = {
  borrowing: 'primary',
  returned: 'success',
  overdue: 'error',
}

const stageOptions = Object.keys(stageMap).map((key) => ({
  title: stageMap[key],
  value: key,
}))

const headers = [
  { title: '借用单号', key: 'rental_no' },
  { title: '手机号', key: 'user_phone' },
  { title: '推车编号', key: 'cart_no' },
  { title: '借出服务点', key: 'borrow_station_name' },
  { title: '归还服务点', key: 'return_station_name' },
  { title: '借出时间', key: 'borrow_time' },
  { title: '归还时间', key: 'return_time' },
  { title: '当前环节', key: 'stage' },
]

const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const loadRentals = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (stageFilter.value) {
      params.stage = stageFilter.value
    }
    if (searchPhone.value) {
      params.user_phone = searchPhone.value
    }
    const res = await axios.get('/rentals', { params })
    rentals.value = res.data.data?.items || res.data.data || res.data || []
  } catch (e) {
    alert('加载借还记录失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRentals()
})
</script>
