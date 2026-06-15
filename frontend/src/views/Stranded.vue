<template>
  <div class="pa-6">
    <h1 class="mb-6">滞留上报与处理</h1>

    <v-card>
      <v-card-text>
        <v-tabs v-model="activeTab" color="primary" density="comfortable" class="mb-4">
          <v-tab value="all">全部</v-tab>
          <v-tab value="reported">待回收</v-tab>
          <v-tab value="recycling">回收中</v-tab>
          <v-tab value="recycled">已回收</v-tab>
        </v-tabs>

        <v-row v-if="activeTab === 'all' || activeTab === 'reported'" class="mb-4">
          <v-col class="d-flex justify-end">
            <v-btn color="error" @click="openReportDialog">
              上报滞留
            </v-btn>
          </v-col>
        </v-row>

        <v-data-table
          :headers="headers"
          :items="filteredItems"
          :items-per-page="10"
          class="elevation-1"
        >
          <template #item.strandedHours="{ item }">
            {{ calculateStrandedHours(item.reportedAt) }}
          </template>
          <template #item.status="{ item }">
            <v-chip :color="statusColorMap[item.status]" size="small">
              {{ statusMap[item.status] }}
            </v-chip>
          </template>
          <template #item.actions="{ item }">
            <v-btn
              v-if="item.status === 'reported'"
              color="warning"
              size="small"
              variant="flat"
              @click="handleStartRecycle(item)"
            >
              开始回收
            </v-btn>
            <v-btn
              v-else-if="item.status === 'recycling'"
              color="success"
              size="small"
              variant="flat"
              @click="handleCompleteRecycle(item)"
            >
              完成回收
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <v-dialog v-model="reportDialogVisible" max-width="500">
      <v-card>
        <v-card-title>上报滞留</v-card-title>
        <v-card-text>
          <v-select
            v-model="form.cart_id"
            label="推车"
            variant="outlined"
            class="mb-4"
            :items="availableCarts"
            item-title="cartNo"
            item-value="id"
          />
          <v-select
            v-model="form.report_station_id"
            label="上报位置服务点"
            variant="outlined"
            class="mb-4"
            :items="stations"
            item-title="name"
            item-value="id"
          />
          <v-text-field
            v-model="form.reporter_name"
            label="上报人姓名"
            variant="outlined"
            class="mb-4"
          />
          <v-text-field
            v-model="form.reporter_phone"
            label="上报人电话"
            variant="outlined"
            class="mb-4"
          />
          <v-textarea
            v-model="form.description"
            label="情况描述"
            variant="outlined"
            class="mb-4"
          />
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="reportDialogVisible = false">取消</v-btn>
          <v-btn color="error" @click="submitReport">提交</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from '@/api/http'
import dayjs from 'dayjs'

interface StrandedRecord {
  id: number
  cartId: number
  cartNo: string
  reportStationId: number
  reportStationName: string
  reporterName?: string
  reporterPhone?: string
  description?: string
  status: 'reported' | 'recycling' | 'recycled'
  reportedAt: string
  recyclingAt?: string
  completedAt?: string
}

interface Cart {
  id: number
  cartNo: string
  status: string
}

interface Station {
  id: number
  name: string
}

const records = ref<StrandedRecord[]>([])
const carts = ref<Cart[]>([])
const stations = ref<Station[]>([])
const activeTab = ref('all')
const reportDialogVisible = ref(false)

const form = ref({
  cart_id: null as number | null,
  report_station_id: null as number | null,
  reporter_name: '',
  reporter_phone: '',
  description: '',
})

const statusMap: Record<string, string> = {
  reported: '待回收',
  recycling: '回收中',
  recycled: '已回收',
}

const statusColorMap: Record<string, string> = {
  reported: 'error',
  recycling: 'warning',
  recycled: 'success',
}

const headers = [
  { title: '推车编号', key: 'cartNo' },
  { title: '上报服务点', key: 'reportStationName' },
  { title: '上报人', key: 'reporterName' },
  { title: '上报时间', key: 'reportedAt' },
  { title: '滞留时长(小时)', key: 'strandedHours' },
  { title: '状态', key: 'status' },
  { title: '操作', key: 'actions', width: '160px' },
]

const availableCarts = computed(() => {
  return carts.value.filter((c) => c.status !== 'transferring')
})

const filteredItems = computed(() => {
  if (activeTab.value === 'all') {
    return records.value
  }
  return records.value.filter((r) => r.status === activeTab.value)
})

const calculateStrandedHours = (reportedAt: string) => {
  const now = dayjs()
  const hours = now.diff(dayjs(reportedAt), 'hour', true)
  return hours.toFixed(1)
}

const loadRecords = async () => {
  try {
    const res = await axios.get('/stranded')
    records.value = res.data.data || res.data || []
  } catch (e) {
    alert('加载滞留记录失败')
  }
}

const loadCarts = async () => {
  try {
    const res = await axios.get('/carts')
    carts.value = res.data.data || res.data || []
  } catch (e) {
    alert('加载推车列表失败')
  }
}

const loadStations = async () => {
  try {
    const res = await axios.get('/stations')
    stations.value = res.data.data || res.data || []
  } catch (e) {
    alert('加载服务点列表失败')
  }
}

const openReportDialog = () => {
  form.value = {
    cart_id: null,
    report_station_id: null,
    reporter_name: '',
    reporter_phone: '',
    description: '',
  }
  reportDialogVisible.value = true
}

const submitReport = async () => {
  if (!form.value.cart_id) {
    alert('请选择推车')
    return
  }
  if (!form.value.report_station_id) {
    alert('请选择上报位置服务点')
    return
  }
  try {
    await axios.post('/stranded', form.value)
    reportDialogVisible.value = false
    loadRecords()
  } catch (e) {
    alert('上报滞留失败')
  }
}

const handleStartRecycle = async (item: StrandedRecord) => {
  try {
    await axios.put(`/stranded/${item.id}/recycle`)
    loadRecords()
  } catch (e) {
    alert('开始回收失败')
  }
}

const handleCompleteRecycle = async (item: StrandedRecord) => {
  try {
    await axios.put(`/stranded/${item.id}/complete`)
    loadRecords()
  } catch (e) {
    alert('完成回收失败')
  }
}

onMounted(() => {
  loadRecords()
  loadCarts()
  loadStations()
})
</script>
