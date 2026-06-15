<template>
  <div class="pa-6">
    <h1 class="mb-6">归还登记</h1>

    <div class="d-flex justify-center">
      <v-card max-width="500" class="w-100">
        <v-card-text>
          <v-select
            v-model="form.rental_no"
            label="选择进行中的借用单"
            variant="outlined"
            class="mb-4"
            :items="activeRentalOptions"
            item-title="title"
            item-value="value"
            return-object="false"
            clearable
          />

          <v-text-field
            v-if="!form.rental_no"
            v-model="form.rental_no"
            label="或手动输入借用单号"
            variant="outlined"
            class="mb-4"
          />

          <v-select
            v-model="form.return_station_id"
            label="归还服务点"
            variant="outlined"
            class="mb-4"
            :items="stationOptions"
            item-title="title"
            item-value="value"
            return-object="false"
          />

          <v-btn color="primary" block @click="submitReturn" :loading="submitting">
            确认归还
          </v-btn>

          <v-alert v-if="returnResult" :type="returnResult.type" class="mt-4">
            {{ returnResult.message }}
          </v-alert>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from '@/api/http'

interface Station {
  id: number
  name: string
  floor: number
  location: string
  safety_stock: number
  is_active: boolean
  current_count: number
}

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

interface ReturnResult {
  type: 'success' | 'warning'
  message: string
}

const stations = ref<Station[]>([])
const activeRentals = ref<Rental[]>([])
const returnResult = ref<ReturnResult | null>(null)
const submitting = ref(false)

const form = ref({
  rental_no: '',
  return_station_id: null as number | null,
})

const stationOptions = computed(() =>
  stations.value.map((s) => ({
    title: s.name,
    value: s.id,
  }))
)

const activeRentalOptions = computed(() =>
  activeRentals.value.map((r) => ({
    title: `${r.rental_no} ${r.user_phone}`,
    value: r.rental_no,
  }))
)

const loadStations = async () => {
  try {
    const res = await axios.get('/stations')
    stations.value = res.data.data?.items || res.data.data || res.data || []
  } catch (e) {
    alert('加载服务点列表失败')
  }
}

const loadActiveRentals = async () => {
  try {
    const res1 = await axios.get('/rentals', { params: { stage: 'borrowing' } })
    const res2 = await axios.get('/rentals', { params: { stage: 'overdue' } })
    const borrowing = res1.data.data?.items || res1.data.data || res1.data || []
    const overdue = res2.data.data?.items || res2.data.data || res2.data || []
    activeRentals.value = [...borrowing, ...overdue]
  } catch (e) {
    alert('加载进行中的借用单失败')
  }
}

const submitReturn = async () => {
  if (!form.value.rental_no) {
    alert('请选择或输入借用单号')
    return
  }
  if (!form.value.return_station_id) {
    alert('请选择归还服务点')
    return
  }
  submitting.value = true
  returnResult.value = null
  try {
    const res = await axios.post('/rentals/return', {
      rental_no: form.value.rental_no,
      return_station_id: form.value.return_station_id,
    })
    const data = res.data.data || res.data
    const isCrossStation = data.borrow_station_id !== data.return_station_id
    if (isCrossStation) {
      returnResult.value = {
        type: 'warning',
        message: '已跨点归还，推车需复位检查后才能重新投放',
      }
    } else {
      returnResult.value = {
        type: 'success',
        message: '归还成功，推车已可再次借出',
      }
    }
    form.value = {
      rental_no: '',
      return_station_id: null,
    }
    loadActiveRentals()
  } catch (e: any) {
    alert(e.response?.data?.detail || '归还失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadStations()
  loadActiveRentals()
})
</script>
