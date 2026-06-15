<template>
  <div class="pa-6">
    <h1 class="mb-6">借出登记</h1>

    <div class="d-flex justify-center">
      <v-card max-width="500" class="w-100">
        <v-card-text>
          <v-text-field
            v-model="form.user_phone"
            label="手机号"
            variant="outlined"
            class="mb-4"
            @blur="checkPhone"
          />

          <v-alert
            v-if="phoneCheckResult !== null"
            :type="phoneCheckResult.can_borrow ? 'success' : 'error'"
            class="mb-4"
          >
            {{ phoneCheckResult.can_borrow ? '该手机号可以借车' : phoneCheckResult.reason }}
          </v-alert>

          <v-alert
            v-if="phoneCheckResult?.has_reservation && !phoneCheckResult.reservation_expired"
            type="info"
            class="mb-4"
          >
            <div>该手机号已有有效预约：</div>
            <div class="mt-1">
              <strong>预约单号：</strong>{{ phoneCheckResult.reservation_no }}
            </div>
            <div>
              <strong>失效时间：</strong>{{ formatTime(phoneCheckResult.expire_time) }}
            </div>
            <div v-if="autoFilled" class="mt-2 text-green font-bold">
              ✓ 已自动填充预约的服务点和推车，请确认后借出
            </div>
          </v-alert>

          <v-alert
            v-if="phoneCheckResult?.has_reservation && phoneCheckResult.reservation_expired"
            type="warning"
            class="mb-4"
          >
            {{ phoneCheckResult.reason }}
          </v-alert>

          <v-select
            v-model="form.borrow_station_id"
            label="借出服务点"
            variant="outlined"
            class="mb-4"
            :items="stationOptions"
            item-title="title"
            item-value="value"
            return-object="false"
          />

          <v-select
            v-model="form.cart_id"
            label="可用推车"
            variant="outlined"
            class="mb-4"
            :items="availableCartOptions"
            item-title="title"
            item-value="value"
            return-object="false"
            :disabled="!form.borrow_station_id"
          />

          <v-btn color="primary" block @click="submitBorrow" :loading="submitting">
            确认借出
          </v-btn>

          <v-alert v-if="successResult" type="success" class="mt-4">
            借出成功！借用单号：{{ successResult.rental_no }}，推车编号：{{ successResult.cart_no }}
          </v-alert>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import axios from '@/api/http'
import dayjs from 'dayjs'

interface Station {
  id: number
  name: string
  floor: number
  location: string
  safety_stock: number
  is_active: boolean
  current_count: number
}

interface Cart {
  id: number
  cart_no: string
  station_id: number
  station_name: string
  cart_type: string
  status: string
  status_display: string
  last_clean_time: string | null
  created_at: string
  updated_at: string
}

interface PhoneCheckResult {
  can_borrow: boolean
  reason: string
  has_reservation?: boolean
  reservation_expired?: boolean
  reservation_no?: string
  cart_id?: number
  expire_time?: string
}

interface BorrowSuccessResult {
  rental_no: string
  cart_no: string
}

const stations = ref<Station[]>([])
const availableCarts = ref<Cart[]>([])
const phoneCheckResult = ref<PhoneCheckResult | null>(null)
const successResult = ref<BorrowSuccessResult | null>(null)
const submitting = ref(false)
const autoFilled = ref(false)

const form = ref({
  user_phone: '',
  borrow_station_id: null as number | null,
  cart_id: null as number | null,
})

const stationOptions = computed(() =>
  stations.value.map((s) => ({
    title: s.name,
    value: s.id,
  }))
)

const availableCartOptions = computed(() => {
  let carts = availableCarts.value
  if (form.value.borrow_station_id) {
    carts = carts.filter((c) => c.station_id === form.value.borrow_station_id)
  }
  return carts
    .filter((c) => {
      if (c.status === 'available') return true
      if (c.status === 'reserved' && phoneCheckResult.value?.cart_id === c.id) return true
      return false
    })
    .map((c) => ({
      title: c.status === 'reserved' ? `${c.cart_no} (您已预约)` : c.cart_no,
      value: c.id,
    }))
})

const formatTime = (time?: string | null) => {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const checkPhone = async () => {
  if (!form.value.user_phone) {
    phoneCheckResult.value = null
    return
  }
  autoFilled.value = false
  try {
    const res = await axios.get(`/rentals/check-phone/${form.value.user_phone}`)
    const data = res.data.data || res.data
    phoneCheckResult.value = data

    if (data.can_borrow && data.has_reservation && !data.reservation_expired && data.cart_id) {
      const reservedCart = availableCarts.value.find((c) => c.id === data.cart_id)
      if (reservedCart) {
        form.value.borrow_station_id = reservedCart.station_id
        form.value.cart_id = reservedCart.id
        autoFilled.value = true
      }
    }
  } catch (e: any) {
    phoneCheckResult.value = {
      can_borrow: false,
      reason: e.response?.data?.detail || '检查手机号失败',
    }
  }
}

const loadStations = async () => {
  try {
    const res = await axios.get('/stations')
    stations.value = res.data.data?.items || res.data.data || res.data || []
  } catch (e) {
    alert('加载服务点列表失败')
  }
}

const loadAvailableCarts = async () => {
  try {
    const res = await axios.get('/carts')
    const allCarts = res.data.data?.items || res.data.data || res.data || []
    availableCarts.value = allCarts.filter((c: Cart) => ['available', 'reserved'].includes(c.status))
  } catch (e) {
    alert('加载可用推车列表失败')
  }
}

const submitBorrow = async () => {
  if (!form.value.user_phone) {
    alert('请输入手机号')
    return
  }
  if (!form.value.borrow_station_id) {
    alert('请选择借出服务点')
    return
  }
  if (!form.value.cart_id) {
    alert('请选择可用推车')
    return
  }
  submitting.value = true
  successResult.value = null
  try {
    const res = await axios.post('/rentals/borrow', {
      user_phone: form.value.user_phone,
      borrow_station_id: form.value.borrow_station_id,
      cart_id: form.value.cart_id,
    })
    const data = res.data.data || res.data
    successResult.value = {
      rental_no: data.rental_no,
      cart_no: data.cart_no,
    }
    form.value = {
      user_phone: '',
      borrow_station_id: null,
      cart_id: null,
    }
    phoneCheckResult.value = null
    autoFilled.value = false
    loadAvailableCarts()
  } catch (e: any) {
    alert(e.response?.data?.detail || '借出失败')
  } finally {
    submitting.value = false
  }
}

watch(
  () => form.value.borrow_station_id,
  () => {
    if (form.value.cart_id) {
      const cart = availableCarts.value.find((c) => c.id === form.value.cart_id)
      if (cart && cart.station_id !== form.value.borrow_station_id) {
        form.value.cart_id = null
      }
    }
  }
)

onMounted(() => {
  loadStations()
  loadAvailableCarts()
})
</script>
