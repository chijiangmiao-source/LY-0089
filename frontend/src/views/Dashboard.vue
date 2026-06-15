<template>
  <div class="pa-6">
    <h1 class="mb-6">调度看板</h1>

    <v-row>
      <v-col cols="2">
        <v-card color="blue-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">推车总数</div>
            <div class="text-h4 font-bold">{{ overview.total_carts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="2">
        <v-card color="green-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">可用推车</div>
            <div class="text-h4 font-bold">{{ overview.available_carts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="2">
        <v-card color="purple-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">预约中推车</div>
            <div class="text-h4 font-bold">{{ overview.reserved_carts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="2">
        <v-card color="orange-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">借出中</div>
            <div class="text-h4 font-bold">{{ overview.borrowed_carts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="2">
        <v-card color="red-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">滞留中</div>
            <div class="text-h4 font-bold">{{ overview.stranded_carts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="2">
        <v-card color="indigo-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">有效预约数</div>
            <div class="text-h4 font-bold">{{ overview.active_reservations || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="8">
        <v-card>
          <v-card-title>各楼层缺车情况</v-card-title>
          <v-data-table
            :headers="floorHeaders"
            :items="floorShortage"
            :items-per-page="5"
            class="elevation-1"
          >
            <template #item.shortage="{ item }">
              <span :class="item.shortage > 0 ? 'text-red font-bold' : ''">{{ item.shortage }}</span>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
      <v-col cols="4">
        <v-card>
          <v-card-title>调拨完成率</v-card-title>
          <v-card-text>
            <div class="mb-4">
              <div class="d-flex justify-space-between mb-2">
                <span>完成进度</span>
                <span class="font-bold">{{ transferRate.completion_rate || 0 }}%</span>
              </div>
              <v-progress-linear
                :model-value="transferRate.completion_rate || 0"
                color="primary"
                height="12"
                rounded
              />
            </div>
            <v-row>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">总数</div>
                <div class="text-h6 font-bold">{{ transferRate.total || 0 }}</div>
              </v-col>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">已完成</div>
                <div class="text-h6 font-bold text-green">{{ transferRate.completed || 0 }}</div>
              </v-col>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">进行中</div>
                <div class="text-h6 font-bold text-orange">{{ transferRate.in_progress || 0 }}</div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="6">
        <v-card>
          <v-card-title>即将超时预约（5分钟内）</v-card-title>
          <v-data-table
            :headers="expiringHeaders"
            :items="expiringReservations"
            :items-per-page="5"
            class="elevation-1"
          >
            <template #item.expire_time="{ item }">
              <span class="text-orange font-bold">
                {{ formatTime(item.expire_time) }}
                <span class="text-caption">（还剩{{ item.minutes_left }}分钟）</span>
              </span>
            </template>
            <template #item.reserve_time="{ item }">
              {{ formatTime(item.reserve_time) }}
            </template>
          </v-data-table>
          <v-alert v-if="expiringReservations.length === 0" type="success" class="ma-4" variant="tonal">
            当前无即将超时的预约
          </v-alert>
        </v-card>
      </v-col>
      <v-col cols="6">
        <v-card>
          <v-card-title>各楼层预约热度（24小时）</v-card-title>
          <v-data-table
            :headers="floorHeatHeaders"
            :items="floorReservationHeat"
            :items-per-page="5"
            class="elevation-1"
          >
            <template #item.total_reservations="{ item }">
              <v-chip
                :color="item.total_reservations > 10 ? 'red' : item.total_reservations > 5 ? 'orange' : 'green'"
                size="small"
                variant="flat"
                dark
              >
                {{ item.total_reservations }}
              </v-chip>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="6">
        <v-card>
          <v-card-title>滞留时长分布</v-card-title>
          <v-data-table
            :headers="strandedHeaders"
            :items="strandedDistribution"
            :items-per-page="10"
            hide-default-footer
            class="elevation-1"
          />
        </v-card>
      </v-col>
      <v-col cols="6">
        <v-card>
          <v-card-title>逾期未还列表</v-card-title>
          <v-data-table
            :headers="overdueHeaders"
            :items="overdueList"
            :items-per-page="5"
            class="elevation-1"
          >
            <template #item.borrow_time="{ item }">
              {{ formatTime(item.borrow_time) }}
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from '@/api/http'
import dayjs from 'dayjs'

interface Overview {
  total_carts?: number
  available_carts?: number
  reserved_carts?: number
  borrowed_carts?: number
  stranded_carts?: number
  transferring_carts?: number
  total_stations?: number
  active_reservations?: number
}

interface FloorShortage {
  floor: string
  total: number
  available: number
  shortage: number
}

interface StrandedItem {
  range: string
  count: number
}

interface TransferRate {
  total?: number
  completed?: number
  in_progress?: number
  pending?: number
  completion_rate?: number
}

interface OverdueItem {
  id: number
  rental_no: string
  user_phone: string
  borrow_time: string
  borrow_station_id: number
  borrow_station_name: string
  cart_id: number
  cart_no: string
  stage: string
  stage_display: string
  overdue_hours: number
}

interface ExpiringReservation {
  id: number
  reservation_no: string
  user_phone: string
  station_id: number
  station_name: string
  cart_id: number | null
  cart_no: string | null
  reserve_time: string
  expire_time: string
  minutes_left: number
}

interface FloorHeat {
  floor: number
  total_reservations: number
  active_reservations: number
  stations: Array<{
    station_id: number
    station_name: string
    total_reservations: number
    active_reservations: number
  }>
}

const overview = ref<Overview>({})
const floorShortage = ref<FloorShortage[]>([])
const strandedDistribution = ref<StrandedItem[]>([])
const transferRate = ref<TransferRate>({})
const overdueList = ref<OverdueItem[]>([])
const expiringReservations = ref<ExpiringReservation[]>([])
const floorReservationHeat = ref<FloorHeat[]>([])

let refreshTimer: ReturnType<typeof setInterval> | null = null

const floorHeaders = [
  { title: '楼层', key: 'floor' },
  { title: '总车数', key: 'total' },
  { title: '可用数', key: 'available' },
  { title: '缺车数', key: 'shortage' },
]

const strandedHeaders = [
  { title: '滞留区间', key: 'range' },
  { title: '数量', key: 'count' },
]

const overdueHeaders = [
  { title: '借用单号', key: 'rental_no' },
  { title: '手机号', key: 'user_phone' },
  { title: '借出时间', key: 'borrow_time' },
  { title: '推车号', key: 'cart_no' },
  { title: '超时(小时)', key: 'overdue_hours' },
]

const expiringHeaders = [
  { title: '预约单号', key: 'reservation_no' },
  { title: '手机号', key: 'user_phone' },
  { title: '服务点', key: 'station_name' },
  { title: '推车号', key: 'cart_no' },
  { title: '预约时间', key: 'reserve_time' },
  { title: '失效时间', key: 'expire_time' },
]

const floorHeatHeaders = [
  { title: '楼层', key: 'floor' },
  { title: '24h预约总数', key: 'total_reservations' },
  { title: '当前预约数', key: 'active_reservations' },
]

const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const loadDashboardData = async () => {
  await Promise.all([
    loadOverview(),
    loadFloorShortage(),
    loadStrandedDistribution(),
    loadTransferRate(),
    loadOverdueList(),
    loadExpiringReservations(),
    loadFloorReservationHeat(),
  ])
}

const loadOverview = async () => {
  try {
    const res = await axios.get('/dashboard/overview')
    overview.value = res.data.data || res.data || {}
  } catch (e) {
    console.error('加载总览数据失败', e)
  }
}

const loadFloorShortage = async () => {
  try {
    const res = await axios.get('/dashboard/floor-shortage')
    floorShortage.value = res.data.data || res.data || []
  } catch (e) {
    console.error('加载楼层缺车数据失败', e)
  }
}

const loadStrandedDistribution = async () => {
  try {
    const res = await axios.get('/dashboard/stranded-distribution')
    strandedDistribution.value = res.data.data || res.data || []
  } catch (e) {
    console.error('加载滞留分布数据失败', e)
  }
}

const loadTransferRate = async () => {
  try {
    const res = await axios.get('/dashboard/transfer-rate')
    transferRate.value = res.data.data || res.data || {}
  } catch (e) {
    console.error('加载调拨完成率数据失败', e)
  }
}

const loadOverdueList = async () => {
  try {
    const res = await axios.get('/dashboard/overdue-list')
    overdueList.value = res.data.data || res.data || []
  } catch (e) {
    console.error('加载逾期列表数据失败', e)
  }
}

const loadExpiringReservations = async () => {
  try {
    const res = await axios.get('/dashboard/upcoming-expiring-reservations?minutes=5')
    expiringReservations.value = res.data.data || res.data || []
  } catch (e) {
    console.error('加载即将超时预约失败', e)
  }
}

const loadFloorReservationHeat = async () => {
  try {
    const res = await axios.get('/dashboard/floor-reservation-heat?hours=24')
    floorReservationHeat.value = res.data.data || res.data || []
  } catch (e) {
    console.error('加载楼层预约热度失败', e)
  }
}

onMounted(() => {
  loadDashboardData()
  refreshTimer = setInterval(loadDashboardData, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>
