<template>
  <div class="pa-6">
    <h1 class="mb-6">跨点调拨管理</h1>

    <v-tabs v-model="activeTab" color="primary" density="comfortable" class="mb-4">
      <v-tab value="orders">调拨单</v-tab>
      <v-tab value="priority">优先调拨队列</v-tab>
    </v-tabs>

    <v-card v-show="activeTab === 'orders'">
      <v-card-text>
        <v-row class="mb-4">
          <v-col cols="4">
            <v-select
              v-model="statusFilter"
              label="状态筛选"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
              :items="statusOptions"
            />
          </v-col>
          <v-col class="d-flex justify-end">
            <v-btn color="primary" @click="openTransferDialog">
              新建调拨单
            </v-btn>
          </v-col>
        </v-row>

        <v-data-table
          :headers="transferHeaders"
          :items="filteredTransfers"
          :items-per-page="10"
          class="elevation-1"
        >
          <template #item.priority="{ item }">
            <v-chip v-if="item.priority === 'urgent'" color="red" size="small">紧急</v-chip>
            <v-chip v-else size="small">普通</v-chip>
          </template>
          <template #item.status="{ item }">
            <v-chip :color="statusColorMap[item.status]" size="small">
              {{ statusMap[item.status] }}
            </v-chip>
          </template>
          <template #item.actions="{ item }">
            <v-btn
              v-if="item.status === 'pending'"
              color="primary"
              size="small"
              variant="flat"
              class="mr-2"
              @click="handleStartTransfer(item)"
            >
              开始调拨
            </v-btn>
            <v-btn
              v-if="item.status === 'pending' || item.status === 'transiting'"
              color="default"
              size="small"
              variant="flat"
              class="mr-2"
              @click="handleCancelTransfer(item)"
            >
              取消
            </v-btn>
            <v-btn
              v-if="item.status === 'transiting'"
              color="success"
              size="small"
              variant="flat"
              @click="handleCompleteTransfer(item)"
            >
              完成调拨
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <v-card v-show="activeTab === 'priority'">
      <v-card-title>低库存服务点</v-card-title>
      <v-card-text>
        <v-data-table
          :headers="priorityHeaders"
          :items="priorityQueue"
          :items-per-page="10"
          class="elevation-1"
        />
      </v-card-text>
    </v-card>

    <v-dialog v-model="transferDialogVisible" max-width="500">
      <v-card>
        <v-card-title>新建调拨单</v-card-title>
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
            v-model="form.from_station_id"
            label="源站"
            variant="outlined"
            class="mb-4"
            :items="stations"
            item-title="name"
            item-value="id"
          />
          <v-select
            v-model="form.to_station_id"
            label="目标站"
            variant="outlined"
            class="mb-4"
            :items="stations"
            item-title="name"
            item-value="id"
          />
          <v-select
            v-model="form.priority"
            label="优先级"
            variant="outlined"
            class="mb-4"
            :items="priorityOptions"
          />
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="transferDialogVisible = false">取消</v-btn>
          <v-btn color="primary" @click="submitTransfer">提交</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from '@/api/http'
import dayjs from 'dayjs'

interface Transfer {
  id: number
  transferNo: string
  cartId: number
  cartNo: string
  fromStationId: number
  fromStationName: string
  toStationId: number
  toStationName: string
  priority: 'normal' | 'urgent'
  status: 'pending' | 'transiting' | 'completed' | 'cancelled'
  createdAt: string
}

interface PriorityStation {
  id: number
  name: string
  floor: number
  safeStock: number
  available: number
  shortage: number
  recommendedSource: string
}

interface Cart {
  id: number
  cartNo: string
}

interface Station {
  id: number
  name: string
}

const transfers = ref<Transfer[]>([])
const priorityQueue = ref<PriorityStation[]>([])
const availableCarts = ref<Cart[]>([])
const stations = ref<Station[]>([])
const activeTab = ref('orders')
const statusFilter = ref<string | null>(null)
const transferDialogVisible = ref(false)

const form = ref({
  cart_id: null as number | null,
  from_station_id: null as number | null,
  to_station_id: null as number | null,
  priority: 'normal' as 'normal' | 'urgent',
})

const statusMap: Record<string, string> = {
  pending: '待调拨',
  transiting: '调拨中',
  completed: '已完成',
  cancelled: '已取消',
}

const statusColorMap: Record<string, string> = {
  pending: 'warning',
  transiting: 'info',
  completed: 'success',
  cancelled: 'default',
}

const statusOptions = Object.keys(statusMap).map((key) => ({
  title: statusMap[key],
  value: key,
}))

const priorityOptions = [
  { title: '普通', value: 'normal' },
  { title: '紧急', value: 'urgent' },
]

const transferHeaders = [
  { title: '调拨单号', key: 'transferNo' },
  { title: '推车号', key: 'cartNo' },
  { title: '源站', key: 'fromStationName' },
  { title: '目标站', key: 'toStationName' },
  { title: '优先级', key: 'priority' },
  { title: '状态', key: 'status' },
  { title: '创建时间', key: 'createdAt' },
  { title: '操作', key: 'actions', width: '240px' },
]

const priorityHeaders = [
  { title: '服务点名', key: 'name' },
  { title: '楼层', key: 'floor' },
  { title: '安全保有量', key: 'safeStock' },
  { title: '当前可用', key: 'available' },
  { title: '缺车数', key: 'shortage' },
  { title: '推荐源站', key: 'recommendedSource' },
]

const filteredTransfers = computed(() => {
  if (!statusFilter.value) {
    return transfers.value
  }
  return transfers.value.filter((t) => t.status === statusFilter.value)
})

const loadTransfers = async () => {
  try {
    const res = await axios.get('/transfers')
    transfers.value = res.data.data || res.data || []
  } catch (e) {
    alert('加载调拨单列表失败')
  }
}

const loadPriorityQueue = async () => {
  try {
    const res = await axios.get('/transfers/priority-queue')
    priorityQueue.value = res.data.data || res.data || []
  } catch (e) {
    alert('加载优先调拨队列失败')
  }
}

const loadAvailableCarts = async () => {
  try {
    const res = await axios.get('/carts', { params: { status: 'available' } })
    availableCarts.value = res.data.data || res.data || []
  } catch (e) {
    alert('加载可用推车列表失败')
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

const openTransferDialog = () => {
  form.value = {
    cart_id: null,
    from_station_id: null,
    to_station_id: null,
    priority: 'normal',
  }
  transferDialogVisible.value = true
}

const submitTransfer = async () => {
  if (!form.value.cart_id) {
    alert('请选择推车')
    return
  }
  if (!form.value.from_station_id) {
    alert('请选择源站')
    return
  }
  if (!form.value.to_station_id) {
    alert('请选择目标站')
    return
  }
  try {
    await axios.post('/transfers', form.value)
    transferDialogVisible.value = false
    loadTransfers()
  } catch (e) {
    alert('新建调拨单失败')
  }
}

const handleStartTransfer = async (item: Transfer) => {
  try {
    await axios.put(`/transfers/${item.id}/start`)
    loadTransfers()
  } catch (e) {
    alert('开始调拨失败')
  }
}

const handleCompleteTransfer = async (item: Transfer) => {
  try {
    await axios.put(`/transfers/${item.id}/complete`)
    loadTransfers()
  } catch (e) {
    alert('完成调拨失败')
  }
}

const handleCancelTransfer = async (item: Transfer) => {
  try {
    await axios.put(`/transfers/${item.id}/cancel`)
    loadTransfers()
  } catch (e) {
    alert('取消调拨失败')
  }
}

onMounted(() => {
  loadTransfers()
  loadPriorityQueue()
  loadAvailableCarts()
  loadStations()
})
</script>
