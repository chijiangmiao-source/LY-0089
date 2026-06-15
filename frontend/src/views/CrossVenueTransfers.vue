<template>
  <div class="pa-6">
    <h1 class="mb-6">跨场地调拨</h1>

    <v-card class="mb-4">
      <v-card-text>
        <v-row>
          <v-col cols="3">
            <v-select
              v-model="filterFromVenue"
              :items="venueOptions"
              label="申请场地"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
              return-object
              @update:model-value="loadList"
            />
          </v-col>
          <v-col cols="3">
            <v-select
              v-model="filterToVenue"
              :items="venueOptions"
              label="目标场地"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
              return-object
              @update:model-value="loadList"
            />
          </v-col>
          <v-col cols="2">
            <v-select
              v-model="filterApproval"
              :items="approvalOptions"
              label="审批状态"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
              @update:model-value="loadList"
            />
          </v-col>
          <v-col cols="2">
            <v-select
              v-model="filterTransport"
              :items="transportOptions"
              label="运输状态"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
              @update:model-value="loadList"
            />
          </v-col>
          <v-col cols="2" class="d-flex align-end justify-end">
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
              发起调拨
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card>
      <v-data-table
        :headers="headers"
        :items="list"
        :items-per-page="10"
        class="elevation-1"
      >
        <template #item.priority_display="{ item }">
          <v-chip :color="item.priority === 'urgent' ? 'red' : 'green'" size="small" variant="flat">
            {{ item.priority_display }}
          </v-chip>
        </template>
        <template #item.approval_status_display="{ item }">
          <v-chip :color="approvalColor(item.approval_status)" size="small" variant="flat">
            {{ item.approval_status_display }}
          </v-chip>
        </template>
        <template #item.transport_status_display="{ item }">
          <v-chip :color="transportColor(item.transport_status)" size="small" variant="flat">
            {{ item.transport_status_display }}
          </v-chip>
        </template>
        <template #item.created_at="{ item }">
          {{ formatTime(item.created_at) }}
        </template>
        <template #item.actions="{ item }">
          <v-btn
            v-if="item.approval_status === 'pending'"
            icon="mdi-check-circle"
            variant="text"
            size="small"
            color="success"
            @click="openApproveDialog(item, 'approved')"
          />
          <v-btn
            v-if="item.approval_status === 'pending'"
            icon="mdi-close-circle"
            variant="text"
            size="small"
            color="error"
            @click="openApproveDialog(item, 'rejected')"
          />
          <v-btn
            v-if="item.approval_status === 'approved' && item.transport_status === 'not_started'"
            icon="mdi-truck-fast"
            variant="text"
            size="small"
            color="primary"
            @click="openStartTransportDialog(item)"
          />
          <v-btn
            v-if="item.transport_status === 'in_transit'"
            icon="mdi-map-marker-check"
            variant="text"
            size="small"
            color="info"
            @click="handleMarkArrived(item)"
          />
          <v-btn
            v-if="item.transport_status === 'arrived'"
            icon="mdi-check-all"
            variant="text"
            size="small"
            color="success"
            @click="handleConfirmReceipt(item)"
          />
          <v-btn
            v-if="item.transport_status === 'not_started' && item.approval_status !== 'cancelled'"
            icon="mdi-cancel"
            variant="text"
            size="small"
            color="grey"
            @click="handleCancel(item)"
          />
          <v-btn icon="mdi-eye" variant="text" size="small" @click="openDetailDialog(item)" />
        </template>
      </v-data-table>
      <v-alert v-if="list.length === 0" type="info" class="ma-4" variant="tonal">
        暂无跨场地调拨记录
      </v-alert>
    </v-card>

    <v-dialog v-model="createDialogVisible" max-width="650">
      <v-card>
        <v-card-title>发起跨场地调拨申请</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="6">
              <v-select
                v-model="createForm.from_venue_id"
                :items="venueOptions"
                label="申请场地"
                variant="outlined"
                class="mb-3"
                item-title="name"
                item-value="id"
              />
            </v-col>
            <v-col cols="6">
              <v-select
                v-model="createForm.to_venue_id"
                :items="venueOptions"
                label="目标场地"
                variant="outlined"
                class="mb-3"
                item-title="name"
                item-value="id"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-select
                v-model="createForm.from_station_id"
                :items="fromStationOptions"
                label="源服务点（可选）"
                variant="outlined"
                class="mb-3"
                item-title="name"
                item-value="id"
                clearable
              />
            </v-col>
            <v-col cols="6">
              <v-select
                v-model="createForm.to_station_id"
                :items="toStationOptions"
                label="目标服务点（可选）"
                variant="outlined"
                class="mb-3"
                item-title="name"
                item-value="id"
                clearable
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-select
                v-model="createForm.cart_id"
                :items="availableCartOptions"
                label="选择推车"
                variant="outlined"
                class="mb-3"
                item-title="display"
                item-value="id"
              />
            </v-col>
            <v-col cols="6">
              <v-select
                v-model="createForm.priority"
                :items="priorityOptions"
                label="优先级"
                variant="outlined"
                class="mb-3"
                item-title="title"
                item-value="value"
              />
            </v-col>
          </v-row>
          <v-text-field
            v-model.number="createForm.quantity"
            type="number"
            label="数量"
            variant="outlined"
            class="mb-3"
          />
          <v-textarea
            v-model="createForm.reason"
            label="调拨原因"
            variant="outlined"
            rows="3"
          />
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="createDialogVisible = false">取消</v-btn>
          <v-btn color="primary" @click="handleCreate">提交申请</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="approveDialogVisible" max-width="450">
      <v-card>
        <v-card-title>{{ approveAction === 'approved' ? '批准调拨' : '拒绝调拨' }}</v-card-title>
        <v-card-text>
          <v-textarea
            v-model="approveForm.approver_comment"
            label="审批意见"
            variant="outlined"
            rows="3"
          />
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="approveDialogVisible = false">取消</v-btn>
          <v-btn :color="approveAction === 'approved' ? 'success' : 'error'" @click="handleApprove">
            确认{{ approveAction === 'approved' ? '批准' : '拒绝' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="startTransportDialogVisible" max-width="450">
      <v-card>
        <v-card-title>发货确认</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="startTransportForm.transporter"
            label="运输方/司机"
            variant="outlined"
            class="mb-3"
          />
          <v-text-field
            v-model="startTransportForm.transport_tracking_no"
            label="运输跟踪号"
            variant="outlined"
          />
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="startTransportDialogVisible = false">取消</v-btn>
          <v-btn color="primary" @click="handleStartTransport">确认发货</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="detailDialogVisible" max-width="600">
      <v-card>
        <v-card-title>调拨单详情 - {{ detailItem?.transfer_no }}</v-card-title>
        <v-card-text>
          <v-row v-if="detailItem">
            <v-col cols="6">
              <div class="text-caption text-medium-emphasis">申请场地</div>
              <div class="font-bold">{{ detailItem.from_venue_name }}</div>
            </v-col>
            <v-col cols="6">
              <div class="text-caption text-medium-emphasis">目标场地</div>
              <div class="font-bold">{{ detailItem.to_venue_name }}</div>
            </v-col>
            <v-col cols="6">
              <div class="text-caption text-medium-emphasis">推车编号</div>
              <div class="font-bold">{{ detailItem.cart_no }}</div>
            </v-col>
            <v-col cols="6">
              <div class="text-caption text-medium-emphasis">优先级</div>
              <v-chip :color="detailItem.priority === 'urgent' ? 'red' : 'green'" size="small">
                {{ detailItem.priority_display }}
              </v-chip>
            </v-col>
            <v-col cols="6">
              <div class="text-caption text-medium-emphasis">审批状态</div>
              <v-chip :color="approvalColor(detailItem.approval_status)" size="small">
                {{ detailItem.approval_status_display }}
              </v-chip>
            </v-col>
            <v-col cols="6">
              <div class="text-caption text-medium-emphasis">运输状态</div>
              <v-chip :color="transportColor(detailItem.transport_status)" size="small">
                {{ detailItem.transport_status_display }}
              </v-chip>
            </v-col>
            <v-col cols="12" v-if="detailItem.reason">
              <div class="text-caption text-medium-emphasis">调拨原因</div>
              <div>{{ detailItem.reason }}</div>
            </v-col>
            <v-col cols="12" v-if="detailItem.approver_comment">
              <div class="text-caption text-medium-emphasis">审批意见</div>
              <div>{{ detailItem.approver_comment }}</div>
            </v-col>
            <v-col cols="6">
              <div class="text-caption text-medium-emphasis">申请人</div>
              <div>{{ detailItem.applicant_name || '-' }}</div>
            </v-col>
            <v-col cols="6">
              <div class="text-caption text-medium-emphasis">审批人</div>
              <div>{{ detailItem.approver_name || '-' }}</div>
            </v-col>
            <v-col cols="6" v-if="detailItem.transporter">
              <div class="text-caption text-medium-emphasis">运输方</div>
              <div>{{ detailItem.transporter }}</div>
            </v-col>
            <v-col cols="6" v-if="detailItem.transport_tracking_no">
              <div class="text-caption text-medium-emphasis">跟踪号</div>
              <div>{{ detailItem.transport_tracking_no }}</div>
            </v-col>
            <v-col cols="6">
              <div class="text-caption text-medium-emphasis">申请时间</div>
              <div>{{ formatTime(detailItem.created_at) }}</div>
            </v-col>
            <v-col cols="6" v-if="detailItem.shipped_at">
              <div class="text-caption text-medium-emphasis">发货时间</div>
              <div>{{ formatTime(detailItem.shipped_at) }}</div>
            </v-col>
            <v-col cols="6" v-if="detailItem.arrived_at">
              <div class="text-caption text-medium-emphasis">到达时间</div>
              <div>{{ formatTime(detailItem.arrived_at) }}</div>
            </v-col>
            <v-col cols="6" v-if="detailItem.confirmed_at">
              <div class="text-caption text-medium-emphasis">确认收货时间</div>
              <div>{{ formatTime(detailItem.confirmed_at) }}</div>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="detailDialogVisible = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import axios from '@/api/http'
import dayjs from 'dayjs'

interface CrossTransfer {
  id: number
  transfer_no: string
  from_venue_id: number
  from_venue_name: string
  to_venue_id: number
  to_venue_name: string
  from_station_id?: number
  from_station_name?: string
  to_station_id?: number
  to_station_name?: string
  cart_id: number
  cart_no: string
  cart_type: string
  priority: string
  priority_display: string
  quantity: number
  reason?: string
  approval_status: string
  approval_status_display: string
  transport_status: string
  transport_status_display: string
  applicant_id?: number
  applicant_name?: string
  approver_id?: number
  approver_name?: string
  approver_comment?: string
  approval_at?: string
  transporter?: string
  transport_tracking_no?: string
  shipped_at?: string
  arrived_at?: string
  confirmed_at?: string
  confirmer_id?: number
  confirmer_name?: string
  created_at: string
  updated_at: string
}

interface Venue {
  id: number
  name: string
}

interface Station {
  id: number
  name: string
  venue_id: number
}

interface Cart {
  id: number
  cart_no: string
  station_name?: string
  venue_name?: string
  status: string
}

const list = ref<CrossTransfer[]>([])
const venues = ref<Venue[]>([])
const stations = ref<Station[]>([])
const carts = ref<Cart[]>([])

const filterFromVenue = ref<Venue | null>(null)
const filterToVenue = ref<Venue | null>(null)
const filterApproval = ref<string | null>(null)
const filterTransport = ref<string | null>(null)

const createDialogVisible = ref(false)
const approveDialogVisible = ref(false)
const startTransportDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const detailItem = ref<CrossTransfer | null>(null)
const currentItem = ref<CrossTransfer | null>(null)
const approveAction = ref<'approved' | 'rejected'>('approved')

const approvalOptions = [
  { title: '待审批', value: 'pending' },
  { title: '已批准', value: 'approved' },
  { title: '已拒绝', value: 'rejected' },
  { title: '已取消', value: 'cancelled' },
]

const transportOptions = [
  { title: '未发货', value: 'not_started' },
  { title: '运输中', value: 'in_transit' },
  { title: '已到达', value: 'arrived' },
  { title: '已确认', value: 'confirmed' },
]

const priorityOptions = [
  { title: '普通', value: 'normal' },
  { title: '紧急', value: 'urgent' },
]

const createForm = ref({
  from_venue_id: null as number | null,
  to_venue_id: null as number | null,
  from_station_id: null as number | null,
  to_station_id: null as number | null,
  cart_id: null as number | null,
  priority: 'normal',
  quantity: 1,
  reason: '',
})

const approveForm = ref({
  approver_comment: '',
})

const startTransportForm = ref({
  transporter: '',
  transport_tracking_no: '',
})

const headers = [
  { title: '调拨单号', key: 'transfer_no' },
  { title: '申请→目标场地', key: 'venue_path' },
  { title: '推车', key: 'cart_no' },
  { title: '优先级', key: 'priority_display' },
  { title: '审批状态', key: 'approval_status_display' },
  { title: '运输状态', key: 'transport_status_display' },
  { title: '申请人', key: 'applicant_name' },
  { title: '申请时间', key: 'created_at' },
  { title: '操作', key: 'actions', width: '220px' },
]

const venueOptions = computed(() => venues.value)

const fromStationOptions = computed(() => {
  if (!createForm.value.from_venue_id) return []
  return stations.value.filter((s) => s.venue_id === createForm.value.from_venue_id)
})

const toStationOptions = computed(() => {
  if (!createForm.value.to_venue_id) return []
  return stations.value.filter((s) => s.venue_id === createForm.value.to_venue_id)
})

const availableCartOptions = computed(() => {
  return carts.value
    .filter((c) => ['available', 'transferring'].includes(c.status))
    .map((c) => ({
      id: c.id,
      display: `${c.cart_no} (${c.venue_name || '未分配'} - ${c.station_name || '未归属'})`,
    }))
})

const approvalColor = (status: string) => {
  const map: Record<string, string> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'error',
    cancelled: 'grey',
  }
  return map[status] || 'grey'
}

const transportColor = (status: string) => {
  const map: Record<string, string> = {
    not_started: 'grey',
    in_transit: 'primary',
    arrived: 'warning',
    confirmed: 'success',
  }
  return map[status] || 'grey'
}

const formatTime = (time: string) => {
  return time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'
}

const loadVenues = async () => {
  try {
    const res = await axios.get('/venues/all?', { params: { is_active: true } })
    venues.value = res.data.data || res.data || []
  } catch (e) {
    console.error('加载场地列表失败', e)
  }
}

const loadStations = async () => {
  try {
    const res = await axios.get('/stations/all', { params: { is_active: true } })
    stations.value = res.data.data || res.data || []
  } catch (e) {
    console.error('加载服务点失败', e)
  }
}

const loadCarts = async () => {
  try {
    const res = await axios.get('/carts/all')
    carts.value = res.data.data || res.data || []
  } catch (e) {
    console.error('加载推车列表失败', e)
  }
}

const loadList = async () => {
  try {
    const params: Record<string, any> = {}
    if (filterFromVenue.value?.id) params.from_venue_id = filterFromVenue.value.id
    if (filterToVenue.value?.id) params.to_venue_id = filterToVenue.value.id
    if (filterApproval.value) params.approval_status = filterApproval.value
    if (filterTransport.value) params.transport_status = filterTransport.value
    const res = await axios.get('/cross-venue-transfers/all', { params })
    list.value = res.data.data || res.data || []
  } catch (e) {
    console.error('加载跨场地调拨列表失败', e)
  }
}

const openCreateDialog = () => {
  createForm.value = {
    from_venue_id: null,
    to_venue_id: null,
    from_station_id: null,
    to_station_id: null,
    cart_id: null,
    priority: 'normal',
    quantity: 1,
    reason: '',
  }
  createDialogVisible.value = true
}

const handleCreate = async () => {
  if (!createForm.value.from_venue_id) {
    alert('请选择申请场地')
    return
  }
  if (!createForm.value.to_venue_id) {
    alert('请选择目标场地')
    return
  }
  if (createForm.value.from_venue_id === createForm.value.to_venue_id) {
    alert('申请场地和目标场地不能相同')
    return
  }
  if (!createForm.value.cart_id) {
    alert('请选择推车')
    return
  }
  try {
    await axios.post('/cross-venue-transfers', createForm.value)
    createDialogVisible.value = false
    loadList()
    loadCarts()
  } catch (e: any) {
    alert(e?.response?.data?.detail || '创建调拨申请失败')
  }
}

const openApproveDialog = (item: CrossTransfer, action: 'approved' | 'rejected') => {
  currentItem.value = item
  approveAction.value = action
  approveForm.value.approver_comment = ''
  approveDialogVisible.value = true
}

const handleApprove = async () => {
  if (!currentItem.value?.id) return
  try {
    await axios.post(`/cross-venue-transfers/${currentItem.value.id}/approve`, {
      approval_status: approveAction.value,
      approver_comment: approveForm.value.approver_comment,
    })
    approveDialogVisible.value = false
    currentItem.value = null
    loadList()
    loadCarts()
  } catch (e: any) {
    alert(e?.response?.data?.detail || '审批操作失败')
  }
}

const openStartTransportDialog = (item: CrossTransfer) => {
  currentItem.value = item
  startTransportForm.value = {
    transporter: '',
    transport_tracking_no: '',
  }
  startTransportDialogVisible.value = true
}

const handleStartTransport = async () => {
  if (!currentItem.value?.id) return
  try {
    await axios.post(`/cross-venue-transfers/${currentItem.value.id}/start-transport`, startTransportForm.value)
    startTransportDialogVisible.value = false
    currentItem.value = null
    loadList()
  } catch (e: any) {
    alert(e?.response?.data?.detail || '发货操作失败')
  }
}

const handleMarkArrived = async (item: CrossTransfer) => {
  if (!confirm('确认已到达目标场地？')) return
  try {
    await axios.post(`/cross-venue-transfers/${item.id}/mark-arrived`)
    loadList()
  } catch (e: any) {
    alert(e?.response?.data?.detail || '标记到达失败')
  }
}

const handleConfirmReceipt = async (item: CrossTransfer) => {
  if (!confirm('确认已收到推车并完成验收？')) return
  try {
    await axios.post(`/cross-venue-transfers/${item.id}/confirm-receipt`)
    loadList()
    loadCarts()
  } catch (e: any) {
    alert(e?.response?.data?.detail || '确认收货失败')
  }
}

const handleCancel = async (item: CrossTransfer) => {
  if (!confirm('确认取消此调拨申请？')) return
  try {
    await axios.post(`/cross-venue-transfers/${item.id}/cancel`)
    loadList()
    loadCarts()
  } catch (e: any) {
    alert(e?.response?.data?.detail || '取消操作失败')
  }
}

const openDetailDialog = (item: CrossTransfer) => {
  detailItem.value = item
  detailDialogVisible.value = true
}

onMounted(() => {
  loadVenues()
  loadStations()
  loadCarts()
  loadList()
})
</script>
