<template>
  <div v-if="isOpen" class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <button class="close-btn" @click="close">×</button>
      <div class="markdown-body" v-html="renderedContent"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
// @ts-ignore
import markdownItKatex from 'markdown-it-katex'
import { algorithmDoc } from '../assets/algorithmDoc'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

md.use(markdownItKatex)

const renderedContent = computed(() => {
  return md.render(algorithmDoc)
})

function close() {
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: white;
  width: 95%;
  max-width: 1400px; /* 控制最大宽度，您可按需调大/调小 */
  height: 90vh;      /* 控制高度占视口比例 */
  border-radius: 12px;
  padding: 3rem;
  position: relative;
  overflow-y: auto;
  box-shadow: 0 20px 50px rgba(0,0,0,0.3);
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #666;
  line-height: 1;
  z-index: 10;
}

.close-btn:hover {
  color: #000;
}

/* Markdown Styles */
.markdown-body {
  color: #333;
  line-height: 1.6;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}

:deep(h1) {
  font-size: 2em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
  margin-bottom: 1rem;
}

:deep(h2) {
  font-size: 1.5em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
}

:deep(h3) {
  font-size: 1.25em;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
}

:deep(p) {
  margin-bottom: 1rem;
}

:deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 1rem;
}

:deep(th), :deep(td) {
  border: 1px solid #dfe2e5;
  padding: 0.6em 1em;
}

:deep(th) {
  background-color: #f6f8fa;
}

:deep(tr:nth-child(2n)) {
  background-color: #f6f8fa;
}

:deep(code) {
  background-color: rgba(27,31,35,0.05);
  border-radius: 3px;
  font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
  padding: 0.2em 0.4em;
}

:deep(pre) {
  background-color: #f6f8fa;
  border-radius: 3px;
  padding: 16px;
  overflow: auto;
}

:deep(pre code) {
  background-color: transparent;
  padding: 0;
}

:deep(blockquote) {
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  padding: 0 1em;
  margin: 0 0 16px 0;
}

:deep(a) {
  color: #0366d6;
  text-decoration: none;
}

:deep(a:hover) {
  text-decoration: underline;
}

/* KaTeX adjustments */
:deep(.katex) {
  font-size: 1em;
  line-height: 1;
}

:deep(.katex-display) {
  margin: 1em 0;
  overflow-x: auto;
  overflow-y: hidden;
}

:deep(.katex .base) {
  position: relative;
}

:deep(.katex .vlist-t) {
  vertical-align: baseline;
}

:deep(.katex sub) {
  font-size: 0.7em;
  vertical-align: baseline;
  position: relative;
  bottom: -0.25em;
}

:deep(.katex sup) {
  font-size: 0.7em;
  vertical-align: baseline;
  position: relative;
  top: -0.5em;
}

:deep(p) {
  margin-bottom: 1rem;
  line-height: 1.8;
  overflow-wrap: break-word;
}

:deep(li) {
  margin-bottom: 0.5rem;
  line-height: 1.8;
}
</style>
