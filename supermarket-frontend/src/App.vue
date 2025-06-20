<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(async () => {
  // 应用启动时检查登录状态
  await authStore.checkAuth()
})
</script>

<style scoped>
#app {
  height: 100%;
}
</style> 