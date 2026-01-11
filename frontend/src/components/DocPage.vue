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

defineEmits<{
  (e: 'back'): void
}>()

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

md.use(markdownItKatex)

const renderedContent = computed(() => md.render(algorithmDoc))
</script>

<style scoped>
.doc-page {
  width: 100%;
  min-height: 100vh;
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
  max-width: 1000px;
  margin: 2rem auto;
  padding: 2rem;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

/* Markdown Styles (simplified version of github-markdown-css) */
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
  line-height: 1.8;
  overflow-wrap: break-word;
}

:deep(li) {
  margin-bottom: 0.5rem;
  line-height: 1.8;
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
</style>
