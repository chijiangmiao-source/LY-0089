<template>
  <div class="pa-6">
    <h1 class="mb-6">推车维修与报废管理</h1>

    <v-tabs v-model="activeTab" color="primary" density="comfortable" class="mb-4">
      <v-tab value="all">全部</v-tab>
      <v-tab value="pending">待维修</v-tab>
      <v-tab value="repairing">维修中</v-tab>
      <v-tab value="completed">已完成</v-tab>
      <v-tab value="scrapped">已报废</v-tab>
    </v-tabs>

    <v-card>
      <v-card-text>
        <v-row v-if="activeTab === 'all' || activeTab === 'pending'" class="mb-4">
          <v-col cols="3">
            <v-select
              v-model="faultTypeFilter"
              label="故障类型筛选"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
              :items="faultTypeOptions"
            />
          </v-col>
          <v-col class="d-flex justify-end">
            <v-btn color="primary" @click="openReportDialog">
              登记维修单
            </v-btn>
          </v-col>
        </v-row>

        <v-data-table
          :headers="headers"
          :items="filteredRecords"
          :items-per-page="10"
          class="elevation-1"
        >
          <template #item.fault_type_display="{ item }">
            <v-chip size="small" variant="flat">
              {{ item.fault_type_display }}
            </v-chip>
          </template>
          <template #item.status="{ item }">
            <v-chip :color="statusColorMap[item.status]" size="small" dark>
              {{ statusMap[item.status] }}
            </v-chip>
          </template>
          <template #item.reported_at="{ item }">
            {{ formatTime(item.reported_at) }}
          </template>
          <template #item.actions="{ item }">
            <v-btn
              v-if="item.status === 'pending'"
              color="warning"
              size="small"
              variant="flat"
              class="mr-2"
              @click="handleStartRepair(item)"
            >
              开始维修
            </v-btn>
            <v-btn
              v-if="item.status === 'pending' || item.status === 'repairing'"
              color="error"
              size="small"
              variant="flat"
              class="mr-2"
              @click="openScrapDialog(item)"
            >
              报废
            </v-btn>
            <v-btn
              v-if="item.status === 'repairing'"
              color="success"
              size="small"
              variant="flat"
              @click="openCompleteDialog(item)"
            >
              完成维修
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <v-dialog v-model="reportDialogVisible" max-width="550">
      <v-card>
        <v-card-title>登记维修单</v-card-title>
        <v-card-text>
          <v-select
            v-model="reportForm.cart_id"
            label="推车（排除维修中/已报废）"
            variant="outlined"
            class="mb-4"
            :items="availableCarts"
            item-title="cart_no"
            item-value="id"
          />
          <v-select
            v-model="reportForm.fault_type"
            label="故障类型"
            variant="outlined"
            class="mb-4"
            :items="faultTypeOptions"
          />
          <v-select
            v-model="reportForm.report_station_id"
            label="报修服务点"
            variant="outlined"
            class="mb-4"
            :items="stations"
            item-title="name"
            item-value="id"
          />
          <v-text-field
            v-model="reportForm.reporter_name"
            label="报修人姓名"
            variant="outlined"
            class="mb-4"
          />
          <v-textarea
            v-model="reportForm.description"
            label="故障描述"
            variant="outlined"
            class="mb-4"
            rows="3"
          />
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="reportDialogVisible = false">取消</v-btn>
          <v-btn color="primary" @click="submitReport">提交报修</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="completeDialogVisible" max-width="550">
      <v-card>
        <v-card-title>完成维修</v-card-title>
        <v-card-text>
          <v-alert type="info" variant="tonal" class="mb-4">
            推车编号：{{ currentRecord?.cart_no }}
          </v-alert>
          <v-textarea
            v-model="completeForm.repair_result"
            label="维修结果（必填）"
            variant="outlined"
            class="mb-4"
            rows="3"
            placeholder="请填写维修过程、更换部件等详细信息"
          />
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="completeDialogVisible = false">取消</v-btn>
          <v-btn color="success" @click="submitComplete">确认完成</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="scrapDialogVisible" max-width="550">
      <v-card>
        <v-card-title>推车报废</v-card-title>
        <v-card-text>
          <v-alert type="warning" variant="tonal" class="mb-4">
            <strong>警告：</strong>推车报废后将从正常运营统计中剔除，此操作不可撤销！
            <br />推车编号：{{ currentRecord?.cart_no }}
          </v-alert>
          <v-textarea
            v-model="scrapForm.repair_result"
            label="报废原因（必填）"
            variant="outlined"
            class="mb-4"
            rows="3"
            placeholder="请填写无法修复的原因"
          />
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="scrapDialogVisible = false">取消</v-btn>
          <v-btn color="error" @click="submitScrap">确认报废</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from '@/api/http'
import dayjs from 'dayjs'

interface MaintenanceRecord {
  id: number
  cart_id: number
  cart_no: string
  fault_type: string
  fault_type_display: string
  report_station_id: number
  report_station_name: string
  reporter_name?: string
  description?: string
  status: 'pending' | 'repairing' | 'completed' | 'scrapped'
  status_display: string
  repair_result?: string
  reported_at: string
  started_at?: string
  completed_at?: string
}

interface Cart {
  id: number
  cart_no: string
  status: string
}

interface Station {
  id: number
  name: string
}

const records = ref<MaintenanceRecord[]>([])
const carts = ref<Cart[]>([])
const stations = ref<Station[]>([])
const activeTab = ref('all')
const faultTypeFilter = ref<string | null>(null)
const reportDialogVisible = ref(false)
const completeDialogVisible = ref(false)
const scrapDialogVisible = ref(false)
const currentRecord = ref<MaintenanceRecord | null>(null)

const reportForm = ref({
  cart_id: null as number | null,
  fault_type: '',
  report_station_id: null as number | null,
  reporter_name: '',
  description: '',
})

const completeForm = ref({
  repair_result: '',
})

const scrapForm = ref({
  repair_result: '',
})

const statusMap: Record<string, string> = {
  pending: '待维修',
  repairing: '维修中',
  completed: '维修完成',
  scrapped: '已报废',
}

const statusColorMap: Record<string, string> = {
  pending: 'warning',
  repairing: 'info',
  completed: 'success',
  scrapped: 'error',
}

const faultTypeOptions = [
  { title: '车轮故障', value: 'wheel' },
  { title: '刹车故障', value: 'brake' },
  { title: '座椅故障', value: 'seat' },
  { title: '把手故障', value: 'handle' },
  { title: '锁具故障', value: 'lock' },
  { title: '车架故障', value: 'frame' },
  { title: '其他故障', value: 'other' },
]

const headers = [
  { title: '维修单ID', key: 'id', width: '80px' },
  { title: '推车编号', key: 'cart_no' },
  { title: '故障类型', key: 'fault_type_display' },
  { title: '报修服务点', key: 'report_station_name' },
  { title: '报修人', key: 'reporter_name' },
  { title: '报修时间', key: 'reported_at' },
  { title: '状态', key: 'status' },
  { title: '操作', key: 'actions', width: '280px' },
]

const availableCarts = computed(() => {
  return carts.value.filter((c) => c.status !== 'maintenance' && c.status !== 'scrapped')
})

const filteredRecords = computed(() => {
  let result = records.value
  if (activeTab.value !== 'all') {
    result = result.filter((r) => r.status === activeTab.value)
  }
  if (faultTypeFilter.value) {
    result = result.filter((r) => r.fault_type === faultTypeFilter.value)
  }
  return result
})

const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const loadRecords = async () => {
  try {
    const res = await axios.get('/maintenance')
    records.value = res.data.data || res.data || []
  } catch (e) {
    alert('加载维修记录失败')
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
  reportForm.value = {
    cart_id: null,
    fault_type: '',
    report_station_id: null,
    reporter_name: '',
    description: '',
  }
  reportDialogVisible.value = true
}

const submitReport = async () => {
  if (!reportForm.value.cart_id) {
    alert('请选择推车')
    return
  }
  if (!reportForm.value.fault_type) {
    alert('请选择故障类型')
    return
  }
  if (!reportForm.value.report_station_id) {
    alert('请选择报修服务点')
    return
  }
  try {
    await axios.post('/maintenance', reportForm.value)
    reportDialogVisible.value = false
    loadRecords()
    loadCarts()
  } catch (e: any) {
    alert(e?.response?.data?.detail || '登记维修单失败')
  }
}

const handleStartRepair = async (item: MaintenanceRecord) => {
  if (!confirm(`确定开始维修推车 ${item.cart_no}？`)) {
    return
  }
  try {
    await axios.put(`/maintenance/${item.id}/start`)
    loadRecords()
  } catch (e) {
    alert('开始维修失败')
  }
}

const openCompleteDialog = (item: MaintenanceRecord) => {
  currentRecord.value = item
  completeForm.value = {
    repair_result: '',
  }
  completeDialogVisible.value = true
}

const submitComplete = async () => {
  if (!completeForm.value.repair_result.trim()) {
    alert('请填写维修结果')
    return
  }
  try {
    await axios.put(`/maintenance/${currentRecord.value!.id}/complete`, completeForm.value)
    completeDialogVisible.value = false
    loadRecords()
    loadCarts()
  } catch (e) {
    alert('完成维修失败')
  }
}

const openScrapDialog = (item: MaintenanceRecord) => {
  currentRecord.value = item
  scrapForm.value = {
    repair_result: '',
  }
  scrapDialogVisible.value = true
}

const submitScrap = async () => {
  if (!scrapForm.value.repair_result.trim()) {
    alert('请填写报废原因')
    return
  }
  if (!confirm(`确定报废推车 ${currentRecord.value!.cart_no}？此操作不可撤销！`)) {
    return
  }
  try {
    await axios.put(`/maintenance/${currentRecord.value!.id}/scrap`, scrapForm.value)
    scrapDialogVisible.value = false
    loadRecords()
    loadCarts()
  } catch (e) {
    alert('报废操作失败')
  }
}

onMounted(() => {
  loadRecords()
  loadCarts()
  loadStations()
})
</script>
