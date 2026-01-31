<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <h1 class="app-title">LLM Eval Studio</h1>
        <el-menu
          :default-active="currentPath"
          mode="horizontal"
          router
          class="nav-menu"
        >
          <el-menu-item index="/cases">用例管理</el-menu-item>
          <el-menu-item index="/evaluation">评测管理</el-menu-item>
          <el-menu-item index="/evaluators">评估器管理</el-menu-item>
          <el-menu-item index="/models">模型管理</el-menu-item>
        </el-menu>
      </div>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const currentPath = computed(() => route.path)
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background-color: #409eff;
  color: white;
  padding: 0 20px;
  display: flex;
  align-items: center;
}

.header-content {
  width: 100%;
  display: flex;
  align-items: center;
}

.app-title {
  margin: 0 40px 0 0;
  font-size: 20px;
  color: white;
}

.nav-menu {
  flex: 1;
  background-color: transparent;
  border: none;
}

.nav-menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.8);
}

.nav-menu :deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.1);
  color: white !important;
}

.nav-menu :deep(.el-menu-item.is-active) {
  background-color: rgba(255, 255, 255, 0.15);
  color: white !important;
  font-weight: 500;
}

.app-main {
  background-color: #f5f7fa;
  overflow-y: auto;
}
</style>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  height: 100vh;
}
</style>
