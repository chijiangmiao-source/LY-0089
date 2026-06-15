<template>
  <div class="pa-6">
    <h1 class="mb-6">调度看板</h1>

    <v-row>
      <v-col cols="3">
        <v-card color="blue-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">推车总数</div>
            <div class="text-h4 font-bold">{{ overview.totalCarts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="3">
        <v-card color="green-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">可用推车</div>
            <div class="text-h4 font-bold">{{ overview.availableCarts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="3">
        <v-card color="orange-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">借出中</div>
            <div class="text-h4 font-bold">{{ overview.borrowedCarts || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="3">
        <v-card color="red-darken-1" dark height="100%">
          <v-card-text>
            <div class="text-caption">滞留中</div>
            <div class="text-h4 font-bold">{{ overview.strandedCarts || 0 }}</div>
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
                <span class="font-bold">{{ transferRate.completionRate || 0 }}%</span>
              </div>
              <v-progress-linear
                :model-value="transferRate.completionRate || 0"
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
                <div class="text-h6 font-bold text-orange">{{ transferRate.inProgress || 0 }}</div>
              </v-col>
            </v-row>
          </v-card-text>
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
            <template #item.borrowTime="{ item }">
              {{ formatTime(item.borrowTime) }}
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from '@/api/http'
import dayjs from 'dayjs'

interface Overview {
  totalCarts?: number
  availableCarts?: number
  borrowedCarts?: number
  strandedCarts?: number
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
  inProgress?: number
  completionRate?: number
}

interface OverdueItem {
  borrowNo: string
  phone: string
  borrowTime: string
  cartNo: string
}

const overview = ref<Overview>({})
const floorShortage = ref<FloorShortage[]>([])
const strandedDistribution = ref<StrandedItem[]>([])
const transferRate = ref<TransferRate>({})
const overdueList = ref<OverdueItem[]>([])

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
  { title: '借用单号', key: 'borrowNo' },
  { title: '手机号', key: 'phone' },
  { title: '借出时间', key: 'borrowTime' },
  { title: '推车号', key: 'cartNo' },
]

const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const loadOverview = async () => {
  try {
    const res = await axios.get('/dashboard/overview')
    overview.value = res.data.data || res.data || {}
  } catch (e) {
    alert('加载总览数据失败')
  }
}

const loadFloorShortage = async () => {
  try {
    const res = await axios.get('/dashboard/floor-shortage')
    floorShortage.value = res.data.data || res.data || []
  } catch (e) {
    alert('加载楼层缺车数据失败')
  }
}

const loadStrandedDistribution = async () => {
  try {
    const res = await axios.get('/dashboard/stranded-distribution')
    strandedDistribution.value = res.data.data || res.data || []
  } catch (e) {
    alert('加载滞留分布数据失败')
  }
}

const loadTransferRate = async () => {
  try {
    const res = await axios.get('/dashboard/transfer-rate')
    transferRate.value = res.data.data || res.data || {}
  } catch (e) {
    alert('加载调拨完成率数据失败')
  }
}

const loadOverdueList = async () => {
  try {
    const res = await axios.get('/dashboard/overdue-list')
    overdueList.value = res.data.data || res.data || []
  } catch (e) {
    alert('加载逾期列表数据失败')
  }
}

onMounted(() => {
  loadOverview()
  loadFloorShortage()
  loadStrandedDistribution()
  loadTransferRate()
  loadOverdueList()
})
</script>
