<template>
  <div class="pa-6">
    <h1 class="mb-6">推车预约</h1>

    <v-row>
      <v-col cols="12" md="5">
        <v-card>
          <v-card-title>创建预约</v-card-title>
          <v-card-text>
            <v-text-field
              v-model="createForm.user_phone"
              label="预约人手机号"
              variant="outlined"
              class="mb-4"
              @blur="checkActiveReservation"
            />

            <v-alert
              v-if="activeReservationCheck.has_active"
              type="warning"
              class="mb-4"
            >
              该手机号已有进行中的预约：{{ activeReservationCheck.reservation?.reservation_no }}，
              失效时间：{{ formatTime(activeReservationCheck.reservation?.expire_time) }}
            </v-alert>

            <v-select
              v-model="createForm.station_id"
              label="预约服务点"
              variant="outlined"
              class="mb-4"
              :items="stationOptions"
              item-title="title"
              item-value="value"
              return-object="false"
              :disabled="activeReservationCheck.has_active"
            />

            <v-select
              v-model="createForm.cart_type"
              label="车型偏好（可选）"
              variant="outlined"
              class="mb-4"
              :items="[
                { title: '标准型', value: 'standard' },
                { title: '大型', value: 'large' },
              ]"
              item-title="title"
              item-value="value"
              clearable
              :disabled="activeReservationCheck.has_active"
            />

            <v-btn
              color="primary"
              block
              @click="submitCreate"
              :loading="creating"
              :disabled="activeReservationCheck.has_active"
            >
              确认预约
            </v-btn>

            <v-alert v-if="createResult" type="success" class="mt-4">
              预约成功！预约单号：{{ createResult.reservation_no }}，
              失效时间：{{ formatTime(createResult.expire_time) }}
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="7">
        <v-card>
          <v-card-title>预约列表</v-card-title>
          <v-card-text>
            <v-row class="mb-4">
              <v-col cols="12" sm="4">
                <v-select
                  v-model="filter.status"
                  label="状态"
                  variant="outlined"
                  :items="statusOptions"
                  item-title="title"
                  item-value="value"
                  clearable
                  density="compact"
                  @change="loadReservations"
                />
              </v-col>
              <v-col cols="12" sm="4">
                <v-text-field
                  v-model="filter.user_phone"
                  label="手机号"
                  variant="outlined"
                  density="compact"
                  @keyup.enter="loadReservations"
                />
              </v-col>
              <v-col cols="12" sm="4" class="d-flex align-end">
                <v-btn color="primary" variant="outlined" block @click="loadReservations">
                  查询
                </v-btn>
              </v-col>
            </v-row>

            <v-data-table
              :headers="reservationHeaders"
              :items="reservations"
              :items-per-page="10"
              class="elevation-1"
              :loading="loading"
            >
              <template #item.status="{ item }">
                <v-chip
                  :color="statusColor(item.status)"
                  size="small"
                  variant="flat"
                >
                  {{ item.status_display }}
                </v-chip>
                <span
                  v-if="item.status === 'active' && item.is_expired"
                  class="text-red ml-2 text-caption"
                >已超时</span>
              </template>

              <template #item.reserve_time="{ item }">
                {{ formatTime(item.reserve_time) }}
              </template>

              <template #item.expire_time="{ item }">
                <span :class="item.status === 'active' && !item.is_expired && isExpiringSoon(item.expire_time) ? 'text-orange font-bold' : ''">
                  {{ formatTime(item.expire_time) }}
                </span>
              </template>

              <template #item.actions="{ item }">
                <v-btn
                  v-if="item.status === 'active' && !item.is_expired"
                  color="error"
                  variant="text"
                  size="small"
                  @click="cancelReservation(item)"
                  :loading="cancellingId === item.id"
                >
                  取消预约
                </v-btn>
                <span v-else>-</span>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from '@/api/http'
import dayjs from 'dayjs'

interface Station {
  id: number
  name: string
  current_count: number
}

interface Reservation {
  id: number
  reservation_no: string
  user_phone: string
  station_id: number
  station_name: string
  cart_id: number | null
  cart_no: string | null
  reserve_time: string
  expire_time: string
  pickup_time: string | null
  status: string
  status_display: string
  is_expired: boolean
}

interface CreateResult {
  reservation_no: string
  expire_time: string
}

interface ActiveCheckResult {
  has_active: boolean
  reservation: Reservation | null
  reason: string
}

const stations = ref<Station[]>([])
const reservations = ref<Reservation[]>([])
const loading = ref(false)
const creating = ref(false)
const cancellingId = ref<number | null>(null)
const createResult = ref<CreateResult | null>(null)
const activeReservationCheck = ref<ActiveCheckResult>({
  has_active: false,
  reservation: null,
  reason: '',
})

const filter = ref({
  status: '',
  user_phone: '',
})

const createForm = ref({
  user_phone: '',
  station_id: null as number | null,
  cart_type: null as string | null,
})

const stationOptions = ref<{ title: string; value: number }[]>([])

const statusOptions = [
  { title: '预约中', value: 'active' },
  { title: '已完成', value: 'completed' },
  { title: '已失效', value: 'expired' },
  { title: '已取消', value: 'cancelled' },
]

const reservationHeaders = [
  { title: '预约单号', key: 'reservation_no', width: '180' },
  { title: '手机号', key: 'user_phone' },
  { title: '服务点', key: 'station_name' },
  { title: '推车号', key: 'cart_no' },
  { title: '状态', key: 'status' },
  { title: '预约时间', key: 'reserve_time' },
  { title: '失效时间', key: 'expire_time' },
  { title: '操作', key: 'actions' },
]

const formatTime = (time?: string | null) => {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const statusColor = (status: string) => {
  const map: Record<string, string> = {
    active: 'primary',
    completed: 'success',
    expired: 'grey',
    cancelled: 'error',
  }
  return map[status] || 'grey'
}

const isExpiringSoon = (expireTime: string) => {
  const diff = dayjs(expireTime).diff(dayjs(), 'minute')
  return diff >= 0 && diff <= 5
}

const checkActiveReservation = async () => {
  if (!createForm.value.user_phone) {
    activeReservationCheck.value = { has_active: false, reservation: null, reason: '' }
    return
  }
  try {
    const res = await axios.get(`/reservations/check-active/${createForm.value.user_phone}`)
    activeReservationCheck.value = res.data.data || res.data || { has_active: false, reservation: null, reason: '' }
  } catch (e) {
    activeReservationCheck.value = { has_active: false, reservation: null, reason: '' }
  }
}

const loadStations = async () => {
  try {
    const res = await axios.get('/stations')
    stations.value = res.data.data?.items || res.data.data || res.data || []
    stationOptions.value = stations.value.map((s) => ({
      title: `${s.name} (可用${s.current_count})`,
      value: s.id,
    }))
  } catch (e) {
    alert('加载服务点列表失败')
  }
}

const loadReservations = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (filter.value.status) {
      params.status = filter.value.status
    }
    if (filter.value.user_phone) {
      params.user_phone = filter.value.user_phone
    }
    const res = await axios.get('/reservations', { params })
    reservations.value = res.data.data?.items || res.data.data || res.data || []
  } catch (e) {
    alert('加载预约列表失败')
  } finally {
    loading.value = false
  }
}

const submitCreate = async () => {
  if (!createForm.value.user_phone) {
    alert('请输入预约人手机号')
    return
  }
  if (!createForm.value.station_id) {
    alert('请选择预约服务点')
    return
  }
  creating.value = true
  createResult.value = null
  try {
    const payload: Record<string, any> = {
      user_phone: createForm.value.user_phone,
      station_id: createForm.value.station_id,
    }
    if (createForm.value.cart_type) {
      payload.cart_type = createForm.value.cart_type
    }
    const res = await axios.post('/reservations', payload)
    const data = res.data.data || res.data
    createResult.value = {
      reservation_no: data.reservation_no,
      expire_time: data.expire_time,
    }
    createForm.value = {
      user_phone: '',
      station_id: null,
      cart_type: null,
    }
    activeReservationCheck.value = { has_active: false, reservation: null, reason: '' }
    loadReservations()
  } catch (e: any) {
    alert(e.response?.data?.detail || '预约失败')
  } finally {
    creating.value = false
  }
}

const cancelReservation = async (item: Reservation) => {
  if (!confirm(`确定要取消预约 ${item.reservation_no} 吗？`)) {
    return
  }
  cancellingId.value = item.id
  try {
    await axios.put(`/reservations/${item.id}/cancel`)
    alert('取消成功')
    loadReservations()
  } catch (e: any) {
    alert(e.response?.data?.detail || '取消失败')
  } finally {
    cancellingId.value = null
  }
}

onMounted(() => {
  loadStations()
  loadReservations()
})
</script>
