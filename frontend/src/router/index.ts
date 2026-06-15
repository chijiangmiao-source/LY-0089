import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/layouts/DefaultLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
      { path: 'venues', name: 'Venues', component: () => import('@/views/Venues.vue') },
      { path: 'stations', name: 'Stations', component: () => import('@/views/Stations.vue') },
      { path: 'carts', name: 'Carts', component: () => import('@/views/Carts.vue') },
      { path: 'reservations', name: 'Reservations', component: () => import('@/views/Reservations.vue') },
      { path: 'borrow', name: 'Borrow', component: () => import('@/views/Borrow.vue') },
      { path: 'return', name: 'Return', component: () => import('@/views/Return.vue') },
      { path: 'rentals', name: 'Rentals', component: () => import('@/views/Rentals.vue') },
      { path: 'stranded', name: 'Stranded', component: () => import('@/views/Stranded.vue') },
      { path: 'transfers', name: 'Transfers', component: () => import('@/views/Transfers.vue') },
      { path: 'cross-venue-transfers', name: 'CrossVenueTransfers', component: () => import('@/views/CrossVenueTransfers.vue') },
      { path: 'cleaning', name: 'Cleaning', component: () => import('@/views/Cleaning.vue') },
      { path: 'maintenance', name: 'Maintenance', component: () => import('@/views/Maintenance.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.token) {
    next({ name: 'Login' })
  } else {
    next()
  }
})

export default router
