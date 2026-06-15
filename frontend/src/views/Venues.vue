<template>
  <div class="pa-6">
    <h1 class="mb-6">场地管理</h1>

    <v-card>
      <v-card-text>
        <v-row class="mb-4">
          <v-col cols="6">
            <v-text-field
              v-model="searchKeyword"
              label="搜索场地名称/地址"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="6" class="d-flex justify-end">
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog()">
              新增场地
            </v-btn>
          </v-col>
        </v-row>

        <v-data-table
          :headers="headers"
          :items="filteredVenues"
          :items-per-page="10"
          class="elevation-1"
        >
          <template #item.venue_type_display="{ item }">
            <v-chip :color="venueTypeColor(item.venue_type)" size="small" variant="flat">
              {{ item.venue_type_display }}
            </v-chip>
          </template>
          <template #item.is_active="{ item }">
            <v-chip :color="item.is_active ? 'green' : 'grey'" size="small" variant="flat">
              {{ item.is_active ? '启用' : '禁用' }}
            </v-chip>
          </template>
          <template #item.created_at="{ item }">
            {{ formatTime(item.created_at) }}
          </template>
          <template #item.actions="{ item }">
            <v-btn icon="mdi-pencil" variant="text" size="small" @click="openDialog(item)" />
            <v-btn icon="mdi-delete" variant="text" size="small" color="error" @click="confirmDelete(item)" />
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <v-dialog v-model="dialogVisible" max-width="600">
      <v-card>
        <v-card-title>{{ isEdit ? '编辑场地' : '新增场地' }}</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="form.name"
            label="场地名称"
            variant="outlined"
            class="mb-3"
          />
          <v-select
            v-model="form.venue_type"
            :items="venueTypeOptions"
            label="场地类型"
            variant="outlined"
            class="mb-3"
          />
          <v-text-field
            v-model="form.address"
            label="地址"
            variant="outlined"
            class="mb-3"
          />
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model="form.contact_person"
                label="联系人"
                variant="outlined"
                class="mb-3"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="form.contact_phone"
                label="联系电话"
                variant="outlined"
                class="mb-3"
              />
            </v-col>
          </v-row>
          <v-text-field
            v-model.number="form.total_floors"
            type="number"
            label="总楼层数"
            variant="outlined"
            class="mb-3"
          />
          <v-textarea
            v-model="form.description"
            label="描述"
            variant="outlined"
            rows="2"
            class="mb-3"
          />
          <v-switch
            v-model="form.is_active"
            label="启用状态"
            color="primary"
            inset
          />
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="dialogVisible = false">取消</v-btn>
          <v-btn color="primary" @click="saveVenue">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="deleteDialogVisible" max-width="400">
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>
          确定要删除场地 "{{ deletingVenue?.name }}" 吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="deleteDialogVisible = false">取消</v-btn>
          <v-btn color="error" @click="deleteVenue">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from '@/api/http'
import dayjs from 'dayjs'

interface Venue {
  id?: number
  name: string
  venue_type: string
  venue_type_display?: string
  address: string
  contact_person?: string
  contact_phone?: string
  total_floors: number
  description?: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

const venues = ref<Venue[]>([])
const searchKeyword = ref('')
const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const isEdit = ref(false)
const deletingVenue = ref<Venue | null>(null)

const venueTypeOptions = [
  { title: '商场', value: 'mall' },
  { title: '园区', value: 'park' },
  { title: '其他', value: 'other' },
]

const form = ref<Venue>({
  name: '',
  venue_type: 'mall',
  address: '',
  contact_person: '',
  contact_phone: '',
  total_floors: 5,
  description: '',
  is_active: true,
})

const headers = [
  { title: '场地名称', key: 'name' },
  { title: '类型', key: 'venue_type_display' },
  { title: '地址', key: 'address' },
  { title: '联系人', key: 'contact_person' },
  { title: '联系电话', key: 'contact_phone' },
  { title: '总楼层', key: 'total_floors' },
  { title: '状态', key: 'is_active' },
  { title: '创建时间', key: 'created_at' },
  { title: '操作', key: 'actions', width: '120px' },
]

const venueTypeColor = (type: string) => {
  const map: Record<string, string> = {
    mall: 'primary',
    park: 'success',
    other: 'info',
  }
  return map[type] || 'grey'
}

const formatTime = (time: string) => {
  return time ? dayjs(time).format('YYYY-MM-DD HH:mm') : ''
}

const filteredVenues = computed(() => {
  if (!searchKeyword.value) return venues.value
  const keyword = searchKeyword.value.toLowerCase()
  return venues.value.filter(
    (v) =>
      v.name.toLowerCase().includes(keyword) ||
      (v.address && v.address.toLowerCase().includes(keyword))
  )
})

const loadVenues = async () => {
  try {
    const res = await axios.get('/venues/all')
    venues.value = res.data.data || res.data || []
  } catch (e) {
    alert('加载场地列表失败')
  }
}

const openDialog = (venue?: Venue) => {
  if (venue) {
    isEdit.value = true
    form.value = { ...venue }
  } else {
    isEdit.value = false
    form.value = {
      name: '',
      venue_type: 'mall',
      address: '',
      contact_person: '',
      contact_phone: '',
      total_floors: 5,
      description: '',
      is_active: true,
    }
  }
  dialogVisible.value = true
}

const saveVenue = async () => {
  if (!form.value.name) {
    alert('请输入场地名称')
    return
  }
  if (!form.value.address) {
    alert('请输入地址')
    return
  }
  try {
    if (isEdit.value && form.value.id) {
      await axios.put(`/venues/${form.value.id}`, form.value)
    } else {
      await axios.post('/venues', form.value)
    }
    dialogVisible.value = false
    loadVenues()
  } catch (e) {
    alert(isEdit.value ? '编辑场地失败' : '新增场地失败')
  }
}

const confirmDelete = (venue: Venue) => {
  deletingVenue.value = venue
  deleteDialogVisible.value = true
}

const deleteVenue = async () => {
  if (!deletingVenue.value?.id) return
  try {
    await axios.delete(`/venues/${deletingVenue.value.id}`)
    deleteDialogVisible.value = false
    deletingVenue.value = null
    loadVenues()
  } catch (e) {
    alert('删除场地失败')
  }
}

onMounted(() => {
  loadVenues()
})
</script>
