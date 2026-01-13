<template>
  <div class="doc-page">
    <div class="header">
      <button class="back-btn" @click="$emit('back')">← 返回主页</button>
      <a href="https://github.com/shadawwuegidua/DevScope" target="_blank" class="github-btn">
        <svg height="20" viewBox="0 0 16 16" version="1.1" width="20" aria-hidden="true" class="github-icon">
          <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
        </svg>
        参与开发
      </a>
    </div>
    <div class="content-container">
      <iframe :src="pdfUrl" class="pdf-frame" title="Algorithm Documentation"></iframe>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineEmits<{
  (e: 'back'): void
}>()

// 添加时间戳防止浏览器缓存旧的 PDF 文件
const pdfUrl = ref(`/DATA_ALGORITHM_THEORY.pdf?t=${new Date().getTime()}`)
</script>

<style scoped>
.doc-page {
  width: 100%;
  height: 100vh;
  background-color: #f8f9fa;
  display: flex;
  flex-direction: column;
}

.header {
  padding: 1rem 2rem;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.back-btn {
  background: none;
  border: 1px solid #ddd;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  color: #333;
  transition: all 0.2s;
}

.back-btn:hover {
  background-color: #f0f0f0;
  border-color: #ccc;
}

.github-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: #24292e;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 600;
  transition: background-color 0.2s;
}

.github-btn:hover {
  background-color: #0366d6;
  text-decoration: none;
}

.github-icon {
  fill: currentColor;
}

.content-container {
  flex: 1;
  width: 100%;
  overflow: hidden;
  background-color: #fff;
}

.pdf-frame {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
