<template>
  <div class="pa-6">
    <h1 class="mb-6">服务点管理</h1>

    <v-card>
      <v-card-text>
        <v-row class="mb-4">
          <v-col cols="6">
            <v-text-field
              v-model="searchKeyword"
              label="搜索服务点名称"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="6" class="d-flex justify-end">
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog()">
              新增服务点
            </v-btn>
          </v-col>
        </v-row>

        <v-data-table
          :headers="headers"
          :items="filteredStations"
          :items-per-page="10"
          class="elevation-1"
        >
          <template #item.status="{ item }">
            <v-chip :color="item.enabled ? 'green' : 'grey'" size="small">
              {{ item.enabled ? '启用' : '禁用' }}
            </v-chip>
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
        <v-card-title>{{ isEdit ? '编辑服务点' : '新增服务点' }}</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="form.name"
            label="名称"
            variant="outlined"
            class="mb-4"
          />
          <v-text-field
            v-model.number="form.floor"
            type="number"
            label="楼层"
            variant="outlined"
            class="mb-4"
          />
          <v-text-field
            v-model="form.location"
            label="位置"
            variant="outlined"
            class="mb-4"
          />
          <v-text-field
            v-model.number="form.safeStock"
            type="number"
            label="安全保有量"
            variant="outlined"
            class="mb-4"
          />
          <v-switch
            v-model="form.enabled"
            label="启用状态"
            color="primary"
            inset
          />
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="dialogVisible = false">取消</v-btn>
          <v-btn color="primary" @click="saveStation">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="deleteDialogVisible" max-width="400">
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>
          确定要删除服务点 "{{ deletingStation?.name }}" 吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="deleteDialogVisible = false">取消</v-btn>
          <v-btn color="error" @click="deleteStation">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from '@/api/http'

interface Station {
  id?: number
  name: string
  floor: number
  location: string
  safeStock: number
  available?: number
  enabled: boolean
}

const stations = ref<Station[]>([])
const searchKeyword = ref('')
const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const isEdit = ref(false)
const deletingStation = ref<Station | null>(null)

const form = ref<Station>({
  name: '',
  floor: 1,
  location: '',
  safeStock: 0,
  enabled: true,
})

const headers = [
  { title: '名称', key: 'name' },
  { title: '楼层', key: 'floor' },
  { title: '位置', key: 'location' },
  { title: '安全保有量', key: 'safeStock' },
  { title: '当前可用', key: 'available' },
  { title: '状态', key: 'status' },
  { title: '操作', key: 'actions', width: '120px' },
]

const filteredStations = computed(() => {
  if (!searchKeyword.value) return stations.value
  const keyword = searchKeyword.value.toLowerCase()
  return stations.value.filter((s) => s.name.toLowerCase().includes(keyword))
})

const loadStations = async () => {
  try {
    const res = await axios.get('/stations')
    stations.value = res.data.data || res.data || []
  } catch (e) {
    alert('加载服务点列表失败')
  }
}

const openDialog = (station?: Station) => {
  if (station) {
    isEdit.value = true
    form.value = { ...station }
  } else {
    isEdit.value = false
    form.value = {
      name: '',
      floor: 1,
      location: '',
      safeStock: 0,
      enabled: true,
    }
  }
  dialogVisible.value = true
}

const saveStation = async () => {
  if (!form.value.name) {
    alert('请输入名称')
    return
  }
  try {
    if (isEdit.value && form.value.id) {
      await axios.put(`/stations/${form.value.id}`, form.value)
    } else {
      await axios.post('/stations', form.value)
    }
    dialogVisible.value = false
    loadStations()
  } catch (e) {
    alert(isEdit.value ? '编辑服务点失败' : '新增服务点失败')
  }
}

const confirmDelete = (station: Station) => {
  deletingStation.value = station
  deleteDialogVisible.value = true
}

const deleteStation = async () => {
  if (!deletingStation.value?.id) return
  try {
    await axios.delete(`/stations/${deletingStation.value.id}`)
    deleteDialogVisible.value = false
    deletingStation.value = null
    loadStations()
  } catch (e) {
    alert('删除服务点失败')
  }
}

onMounted(() => {
  loadStations()
})
</script>
