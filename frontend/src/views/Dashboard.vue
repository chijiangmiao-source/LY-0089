<template>
  <div class="pa-6">
    <h1 class="mb-6">调度看板</h1>

    <v-row>
      <v-col cols="1.5">
        <v-card color="blue-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">推车总数</div>
            <div class="text-h4 font-bold">{{ overview.total_carts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="1.5">
        <v-card color="green-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">可用推车</div>
            <div class="text-h4 font-bold">{{ overview.available_carts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="1.5">
        <v-card color="purple-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">预约中</div>
            <div class="text-h4 font-bold">{{ overview.reserved_carts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="1.5">
        <v-card color="orange-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">借出中</div>
            <div class="text-h4 font-bold">{{ overview.borrowed_carts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="1.5">
        <v-card color="red-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">滞留中</div>
            <div class="text-h4 font-bold">{{ overview.stranded_carts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="1.5">
        <v-card color="brown-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">维修中</div>
            <div class="text-h4 font-bold">{{ overview.maintenance_carts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="1.5">
        <v-card color="grey-darken-3" dark height="100%">
          <v-card-text>
            <div class="text-caption">已报废</div>
            <div class="text-h4 font-bold">{{ overview.scrapped_carts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="1.5">
        <v-card color="indigo-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">有效预约</div>
            <div class="text-h4 font-bold">{{ overview.active_reservations || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="7">
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
      <v-col cols="5">
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
          <v-card-title>各楼层故障分布</v-card-title>
          <v-data-table
            :headers="floorFaultHeaders"
            :items="floorFaultDistribution"
            :items-per-page="5"
            class="elevation-1"
          >
            <template #item.total_faults="{ item }">
              <v-chip
                :color="item.total_faults > 5 ? 'red' : item.total_faults > 2 ? 'orange' : 'green'"
                size="small"
                variant="flat"
                dark
              >
                {{ item.total_faults }}
              </v-chip>
            </template>
            <template #item.pending_count="{ item }">
              <span v-if="item.pending_count > 0" class="text-warning font-bold">
                {{ item.pending_count }}
              </span>
              <span v-else>{{ item.pending_count }}</span>
            </template>
            <template #item.repairing_count="{ item }">
              <span v-if="item.repairing_count > 0" class="text-info font-bold">
                {{ item.repairing_count }}
              </span>
              <span v-else>{{ item.repairing_count }}</span>
            </template>
          </v-data-table>
          <v-alert v-if="floorFaultDistribution.length === 0" type="success" class="ma-4" variant="tonal">
            当前无故障记录
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
    </v-row>

    <v-row>
      <v-col cols="12">
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

    <v-divider class="my-6" />
    <h2 class="mb-4 text-primary">多场地统一调度</h2>

    <v-row>
      <v-col cols="8">
        <v-card>
          <v-card-title>各场地运营概览</v-card-title>
          <v-data-table
            :headers="venueOverviewHeaders"
            :items="venueOverviewList"
            :items-per-page="5"
            class="elevation-1"
          >
            <template #item.venue_type_display="{ item }">
              <v-chip
                :color="item.venue_type === 'mall' ? 'primary' : item.venue_type === 'park' ? 'success' : 'info'"
                size="small"
                variant="flat"
              >
                {{ item.venue_type_display }}
              </v-chip>
            </template>
            <template #item.shortage_count="{ item }">
              <span :class="item.shortage_count > 0 ? 'text-red font-bold' : ''">
                {{ item.shortage_count }}
              </span>
            </template>
            <template #item.today_borrow_count="{ item }">
              <v-chip size="small" variant="flat" color="blue">借{{ item.today_borrow_count }}</v-chip>
              <v-chip size="small" variant="flat" color="green" class="ml-1">还{{ item.today_return_count }}</v-chip>
            </template>
          </v-data-table>
          <v-alert v-if="venueOverviewList.length === 0" type="info" class="ma-4" variant="tonal">
            暂无场地数据，请先在场地管理中创建场地
          </v-alert>
        </v-card>
      </v-col>
      <v-col cols="4">
        <v-card>
          <v-card-title>跨场地调拨完成率（30天）</v-card-title>
          <v-card-text>
            <div class="mb-4">
              <div class="d-flex justify-space-between mb-2">
                <span>完成进度</span>
                <span class="font-bold">{{ crossTransferRate.completion_rate || 0 }}%</span>
              </div>
              <v-progress-linear
                :model-value="crossTransferRate.completion_rate || 0"
                color="deep-purple"
                height="12"
                rounded
              />
            </div>
            <v-row>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">总申请</div>
                <div class="text-h6 font-bold">{{ crossTransferRate.total || 0 }}</div>
              </v-col>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">已完成</div>
                <div class="text-h6 font-bold text-green">{{ crossTransferRate.confirmed || 0 }}</div>
              </v-col>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">运输中</div>
                <div class="text-h6 font-bold text-primary">{{ crossTransferRate.in_transit || 0 }}</div>
              </v-col>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">待审批</div>
                <div class="text-h6 font-bold text-warning">{{ crossTransferRate.pending_approval || 0 }}</div>
              </v-col>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">紧急单</div>
                <div class="text-h6 font-bold text-red">{{ crossTransferRate.urgent_count || 0 }}</div>
              </v-col>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">平均耗时</div>
                <div class="text-h6 font-bold">{{ crossTransferRate.avg_transport_hours || 0 }}h</div>
              </v-col>
            </v-row>
            <v-divider class="my-3" />
            <div class="text-subtitle-2 font-bold mb-2">各场地调拨情况</div>
            <v-data-table
              :headers="venueTransferHeaders"
              :items="crossTransferRate.by_venue || []"
              :items-per-page="5"
              density="compact"
              hide-default-footer
              class="elevation-0"
            />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            跨场地缺车预警
            <v-spacer />
            <v-chip color="red" size="small" variant="flat">
              {{ crossVenueShortage.reduce((sum, v) => sum + v.shortage, 0) }} 台总缺车
            </v-chip>
          </v-card-title>
          <v-data-table
            :headers="shortageHeaders"
            :items="crossVenueShortage"
            :items-per-page="5"
            class="elevation-1"
          >
            <template #item.shortage="{ item }">
              <v-chip
                :color="item.shortage >= item.total_safety_stock * 0.3 ? 'red' : 'orange'"
                size="small"
                variant="flat"
                dark
              >
                缺 {{ item.shortage }}
              </v-chip>
            </template>
            <template #item.urgent_need="{ item }">
              <v-chip v-if="item.urgent_need > 0" color="red" size="small" variant="flat">
                紧急 {{ item.urgent_need }}
              </v-chip>
              <span v-else>-</span>
            </template>
            <template #item.affected_stations="{ item }">
              <div v-for="s in item.affected_stations.slice(0, 3)" :key="s.station_id" class="d-flex align-center mb-1">
                <span class="text-caption">{{ s.floor }}F-{{ s.station_name }}</span>
                <v-chip
                  :color="s.shortage >= s.safety_stock * 0.5 ? 'red' : 'orange'"
                  size="x-small"
                  variant="flat"
                  class="ml-2"
                >
                  缺{{ s.shortage }}
                </v-chip>
              </div>
              <span v-if="item.affected_stations.length > 3" class="text-caption text-medium-emphasis">
                另有 {{ item.affected_stations.length - 3 }} 个服务点缺车...
              </span>
            </template>
          </v-data-table>
          <v-alert v-if="crossVenueShortage.length === 0" type="success" class="ma-4" variant="tonal">
            各场地库存充足，暂无缺车预警
          </v-alert>
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
  maintenance_carts?: number
  scrapped_carts?: number
  total_stations?: number
  active_reservations?: number
}

interface FloorShortage {
  floor: string
  total_carts: number
  available_carts: number
  shortage: number
}

interface StrandedItem {
  range: string
  count: number
}

interface TransferRate {
  total_transfers?: number
  completed_transfers?: number
  in_progress_transfers?: number
  pending_transfers?: number
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

interface FloorFault {
  floor: number
  total_faults: number
  pending_count: number
  repairing_count: number
  stations: Array<{
    station_id: number
    station_name: string
    total_faults: number
    pending_count: number
    repairing_count: number
  }>
}

interface VenueOverview {
  venue_id: number
  venue_name: string
  venue_type: string
  venue_type_display: string
  total_carts: number
  available_carts: number
  borrowed_carts: number
  reserved_carts: number
  stranded_carts: number
  maintenance_carts: number
  total_stations: number
  active_reservations: number
  today_borrow_count: number
  today_return_count: number
  pending_maintenance: number
  shortage_count: number
}

interface CrossVenueShortage {
  venue_id: number
  venue_name: string
  total_safety_stock: number
  current_available: number
  shortage: number
  urgent_need: number
  affected_stations: Array<{
    station_id: number
    station_name: string
    floor: number
    safety_stock: number
    current_available: number
    shortage: number
  }>
}

interface CrossVenueTransferRate {
  total_cross_transfers?: number
  pending_approval?: number
  approved?: number
  rejected?: number
  in_transit?: number
  arrived?: number
  confirmed?: number
  completion_rate?: number
  urgent_count?: number
  avg_transport_hours?: number
  total?: number
  by_venue?: Array<{
    venue_id: number
    venue_name: string
    outgoing_total: number
    outgoing_confirmed: number
    outgoing_completion_rate: number
    incoming_total: number
    incoming_pending: number
  }>
}

const overview = ref<Overview>({})
const floorShortage = ref<FloorShortage[]>([])
const strandedDistribution = ref<StrandedItem[]>([])
const transferRate = ref<TransferRate>({})
const overdueList = ref<OverdueItem[]>([])
const expiringReservations = ref<ExpiringReservation[]>([])
const floorReservationHeat = ref<FloorHeat[]>([])
const floorFaultDistribution = ref<FloorFault[]>([])
const venueOverviewList = ref<VenueOverview[]>([])
const crossVenueShortage = ref<CrossVenueShortage[]>([])
const crossTransferRate = ref<CrossVenueTransferRate>({})

let refreshTimer: ReturnType<typeof setInterval> | null = null

const floorHeaders = [
  { title: '楼层', key: 'floor' },
  { title: '总车数', key: 'total_carts' },
  { title: '可用数', key: 'available_carts' },
  { title: '缺车数', key: 'shortage' },
]

const floorFaultHeaders = [
  { title: '楼层', key: 'floor' },
  { title: '故障总数', key: 'total_faults' },
  { title: '待维修', key: 'pending_count' },
  { title: '维修中', key: 'repairing_count' },
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

const venueOverviewHeaders = [
  { title: '场地名称', key: 'venue_name' },
  { title: '类型', key: 'venue_type_display' },
  { title: '总推车', key: 'total_carts' },
  { title: '可用', key: 'available_carts' },
  { title: '借出', key: 'borrowed_carts' },
  { title: '服务点', key: 'total_stations' },
  { title: '今日借/还', key: 'today_borrow_count' },
  { title: '待维修', key: 'pending_maintenance' },
  { title: '缺车数', key: 'shortage_count' },
]

const venueTransferHeaders = [
  { title: '场地', key: 'venue_name' },
  { title: '发出', key: 'outgoing_total' },
  { title: '发出完成率', key: 'outgoing_completion_rate' },
  { title: '收到', key: 'incoming_total' },
]

const shortageHeaders = [
  { title: '场地名称', key: 'venue_name' },
  { title: '安全保有总量', key: 'total_safety_stock' },
  { title: '当前可用', key: 'current_available' },
  { title: '缺车数', key: 'shortage' },
  { title: '紧急需求', key: 'urgent_need' },
  { title: '受影响服务点', key: 'affected_stations' },
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
    loadFloorFaultDistribution(),
    loadVenueOverview(),
    loadCrossVenueShortage(),
    loadCrossVenueTransferRate(),
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
    const data = res.data.data || res.data || {}
    strandedDistribution.value = [
      { range: '< 1小时', count: data.less_than_1h || 0 },
      { range: '1-4小时', count: data.one_to_4h || 0 },
      { range: '4-12小时', count: data.four_to_12h || 0 },
      { range: '> 12小时', count: data.more_than_12h || 0 },
    ]
  } catch (e) {
    console.error('加载滞留分布数据失败', e)
  }
}

const loadTransferRate = async () => {
  try {
    const res = await axios.get('/dashboard/transfer-rate')
    const data = res.data.data || res.data || {}
    transferRate.value = {
      total_transfers: data.total_transfers,
      completed_transfers: data.completed_transfers,
      in_progress_transfers: data.in_progress_transfers,
      pending_transfers: data.pending_transfers,
      completion_rate: data.completion_rate,
    }
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

const loadFloorFaultDistribution = async () => {
  try {
    const res = await axios.get('/dashboard/floor-fault-distribution')
    floorFaultDistribution.value = res.data.data || res.data || []
  } catch (e) {
    console.error('加载楼层故障分布失败', e)
  }
}

const loadVenueOverview = async () => {
  try {
    const res = await axios.get('/dashboard/venue-overview')
    venueOverviewList.value = res.data.data || res.data || []
  } catch (e) {
    console.error('加载各场地运营概览失败', e)
  }
}

const loadCrossVenueShortage = async () => {
  try {
    const res = await axios.get('/dashboard/cross-venue-shortage')
    crossVenueShortage.value = res.data.data || res.data || []
  } catch (e) {
    console.error('加载跨场地缺车预警失败', e)
  }
}

const loadCrossVenueTransferRate = async () => {
  try {
    const res = await axios.get('/dashboard/cross-venue-transfer-rate?days=30')
    const data = res.data.data || res.data || {}
    crossTransferRate.value = {
      total_cross_transfers: data.total_cross_transfers,
      pending_approval: data.pending_approval,
      approved: data.approved,
      rejected: data.rejected,
      in_transit: data.in_transit,
      arrived: data.arrived,
      confirmed: data.confirmed,
      completion_rate: data.completion_rate,
      urgent_count: data.urgent_count,
      avg_transport_hours: data.avg_transport_hours,
      total: data.total_cross_transfers,
      by_venue: data.by_venue,
    }
  } catch (e) {
    console.error('加载跨场地调拨完成率失败', e)
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
