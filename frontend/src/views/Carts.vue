<template>
  <div class="pa-6">
    <h1 class="mb-6">推车档案</h1>

    <v-card>
      <v-card-text>
        <v-row class="mb-4">
          <v-col cols="4">
            <v-text-field
              v-model="searchKeyword"
              label="搜索推车编号"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="4">
            <v-select
              v-model="statusFilter"
              label="按状态筛选"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
              :items="statusOptions"
            />
          </v-col>
          <v-col cols="4" class="d-flex justify-end">
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog()">
              新增推车
            </v-btn>
          </v-col>
        </v-row>

        <v-data-table
          :headers="headers"
          :items="filteredCarts"
          :items-per-page="10"
          class="elevation-1"
        >
          <template #item.cartType="{ item }">
            {{ cartTypeMap[item.cartType] || item.cartType }}
          </template>
          <template #item.status="{ item }">
            <v-chip :color="statusColorMap[item.status]" size="small">
              {{ statusMap[item.status] || item.status }}
            </v-chip>
          </template>
          <template #item.lastCleanedAt="{ item }">
            {{ item.lastCleanedAt ? formatTime(item.lastCleanedAt) : '-' }}
          </template>
          <template #item.actions="{ item }">
            <v-btn icon="mdi-pencil" variant="text" size="small" @click="openDialog(item)" />
            <v-btn icon="mdi-delete" variant="text" size="small" color="error" @click="confirmDelete(item)" />
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <v-dialog v-model="dialogVisible" max-width="500">
      <v-card>
        <v-card-title>{{ isEdit ? '编辑推车' : '新增推车' }}</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="form.cartNo"
            label="推车编号"
            variant="outlined"
            class="mb-4"
          />
          <v-select
            v-model="form.cartType"
            label="车型"
            variant="outlined"
            class="mb-4"
            :items="cartTypeOptions"
          />
          <v-select
            v-model="form.stationId"
            label="所属服务点"
            variant="outlined"
            class="mb-4"
            :items="stationOptions"
            item-title="name"
            item-value="id"
          />
          <v-select
            v-model="form.status"
            label="状态"
            variant="outlined"
            class="mb-4"
            :items="statusOptions"
          />
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="dialogVisible = false">取消</v-btn>
          <v-btn color="primary" @click="saveCart">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="deleteDialogVisible" max-width="400">
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>
          确定要删除推车 "{{ deletingCart?.cartNo }}" 吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="deleteDialogVisible = false">取消</v-btn>
          <v-btn color="error" @click="deleteCart">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from '@/api/http'
import dayjs from 'dayjs'

interface Cart {
  id?: number
  cartNo: string
  cartType: 'standard' | 'large'
  stationId: number | null
  stationName?: string
  status: 'available' | 'borrowed' | 'stranded' | 'transferring' | 'cleaning' | 'reset_check'
  lastCleanedAt?: string
}

interface Station {
  id: number
  name: string
}

const carts = ref<Cart[]>([])
const stations = ref<Station[]>([])
const searchKeyword = ref('')
const statusFilter = ref<string | null>(null)
const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const isEdit = ref(false)
const deletingCart = ref<Cart | null>(null)

const form = ref<Cart>({
  cartNo: '',
  cartType: 'standard',
  stationId: null,
  status: 'available',
})

const statusMap: Record<string, string> = {
  available: '可用',
  borrowed: '借出中',
  stranded: '滞留',
  transferring: '调拨中',
  cleaning: '清洁中',
  reset_check: '复位检查中',
}

const statusColorMap: Record<string, string> = {
  available: 'success',
  borrowed: 'primary',
  stranded: 'error',
  transferring: 'warning',
  cleaning: 'info',
  reset_check: 'warning',
}

const cartTypeMap: Record<string, string> = {
  standard: '标准款',
  large: '大号款',
}

const statusOptions = Object.keys(statusMap).map((key) => ({
  title: statusMap[key],
  value: key,
}))

const cartTypeOptions = Object.keys(cartTypeMap).map((key) => ({
  title: cartTypeMap[key],
  value: key,
}))

const stationOptions = computed(() => stations.value)

const headers = [
  { title: '推车编号', key: 'cartNo' },
  { title: '车型', key: 'cartType' },
  { title: '所属服务点', key: 'stationName' },
  { title: '状态', key: 'status' },
  { title: '最近清洁时间', key: 'lastCleanedAt' },
  { title: '操作', key: 'actions', width: '120px' },
]

const filteredCarts = computed(() => {
  let result = carts.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter((c) => c.cartNo.toLowerCase().includes(keyword))
  }
  if (statusFilter.value) {
    result = result.filter((c) => c.status === statusFilter.value)
  }
  return result
})

const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
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

const openDialog = (cart?: Cart) => {
  if (cart) {
    isEdit.value = true
    form.value = { ...cart }
  } else {
    isEdit.value = false
    form.value = {
      cartNo: '',
      cartType: 'standard',
      stationId: null,
      status: 'available',
    }
  }
  dialogVisible.value = true
}

const saveCart = async () => {
  if (!form.value.cartNo) {
    alert('请输入推车编号')
    return
  }
  try {
    if (isEdit.value && form.value.id) {
      await axios.put(`/carts/${form.value.id}`, form.value)
    } else {
      await axios.post('/carts', form.value)
    }
    dialogVisible.value = false
    loadCarts()
  } catch (e) {
    alert(isEdit.value ? '编辑推车失败' : '新增推车失败')
  }
}

const confirmDelete = (cart: Cart) => {
  deletingCart.value = cart
  deleteDialogVisible.value = true
}

const deleteCart = async () => {
  if (!deletingCart.value?.id) return
  try {
    await axios.delete(`/carts/${deletingCart.value.id}`)
    deleteDialogVisible.value = false
    deletingCart.value = null
    loadCarts()
  } catch (e) {
    alert('删除推车失败')
  }
}

onMounted(() => {
  loadCarts()
  loadStations()
})
</script>
