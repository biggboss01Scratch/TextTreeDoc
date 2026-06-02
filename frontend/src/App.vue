<script setup>
import { computed, onMounted, ref } from 'vue'

const API_BASE =
  import.meta.env.VITE_API_BASE ||
  (window.location.port === '5173' ? 'http://127.0.0.1:8000' : window.location.origin)

const texts = ref([])
const keyword = ref('')
const newText = ref({
  title: '',
  keywords: '',
  content: '',
})
const topic = ref('开源许可证分析报告')
const currentTree = ref(null)
const selectedText = ref(null)
const downloadUrl = ref('')
const notice = ref('')
const loading = ref(false)
const uploadFile = ref(null)

const treeJson = computed(() => (currentTree.value ? JSON.stringify(currentTree.value, null, 2) : ''))

function setNotice(message) {
  notice.value = message
  window.clearTimeout(setNotice.timer)
  setNotice.timer = window.setTimeout(() => {
    notice.value = ''
  }, 3000)
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || '请求失败')
  }
  return response.json()
}

async function loadTexts() {
  const query = keyword.value.trim() ? `?keyword=${encodeURIComponent(keyword.value.trim())}` : ''
  texts.value = await apiFetch(`/texts${query}`)
}

async function addText() {
  if (!newText.value.title.trim() || !newText.value.content.trim()) {
    setNotice('请填写标题和正文')
    return
  }
  loading.value = true
  try {
    await apiFetch('/texts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newText.value),
    })
    newText.value = { title: '', keywords: '', content: '' }
    await loadTexts()
    setNotice('文本已入库')
  } catch (error) {
    setNotice(error.message)
  } finally {
    loading.value = false
  }
}

async function removeText(id) {
  loading.value = true
  try {
    await apiFetch(`/texts/${id}`, { method: 'DELETE' })
    if (selectedText.value?.id === id) selectedText.value = null
    await loadTexts()
    setNotice('文本已删除')
  } catch (error) {
    setNotice(error.message)
  } finally {
    loading.value = false
  }
}

async function uploadSelectedFile() {
  if (!uploadFile.value) {
    setNotice('请选择文件')
    return
  }
  const formData = new FormData()
  formData.append('file', uploadFile.value)
  loading.value = true
  try {
    await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    }).then(async (response) => {
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '上传失败' }))
        throw new Error(error.detail || '上传失败')
      }
      return response.json()
    })
    uploadFile.value = null
    document.querySelector('#fileInput').value = ''
    await loadTexts()
    setNotice('文件已解析入库')
  } catch (error) {
    setNotice(error.message)
  } finally {
    loading.value = false
  }
}

/**
 * 根据用户输入的主题请求后端生成文档结构树。
 * 请求成功后，将返回的 JSON 结构渲染到页面中。
 */
async function generateTree() {
  if (!topic.value.trim()) {
    setNotice('请输入文档主题')
    return
  }
  loading.value = true
  downloadUrl.value = ''
  try {
    currentTree.value = await apiFetch('/documents/tree', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic: topic.value.trim(), use_llm: false }),
    })
    setNotice('结构树已生成')
  } catch (error) {
    setNotice(error.message)
  } finally {
    loading.value = false
  }
}

/**
 * 调用后端接口，根据当前文档树生成 Word 文件。
 * 成功后显示下载链接。
 */
async function generateDocx() {
  if (!currentTree.value) {
    setNotice('请先生成文档结构树')
    return
  }
  loading.value = true
  try {
    const result = await apiFetch('/documents/docx', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: currentTree.value.title, tree: currentTree.value }),
    })
    downloadUrl.value = `${API_BASE}${result.download_url}`
    setNotice('Word 文档已生成')
  } catch (error) {
    setNotice(error.message)
  } finally {
    loading.value = false
  }
}

onMounted(loadTexts)
</script>

<template>
  <main class="shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">TextTreeDoc</p>
        <h1>文档结构树与 Word 自动生成</h1>
      </div>
      <span class="status" :class="{ busy: loading }">{{ loading ? '处理中' : '就绪' }}</span>
    </header>

    <p v-if="notice" class="notice">{{ notice }}</p>

    <section class="workspace">
      <aside class="panel library-panel">
        <div class="panel-head">
          <h2>文本库</h2>
          <button type="button" @click="loadTexts">刷新</button>
        </div>
        <div class="search-row">
          <input v-model="keyword" type="search" placeholder="搜索标题、关键词或正文" @keyup.enter="loadTexts" />
          <button type="button" @click="loadTexts">搜索</button>
        </div>

        <div class="text-list">
          <article
            v-for="item in texts"
            :key="item.id"
            class="text-item"
            :class="{ active: selectedText?.id === item.id }"
            @click="selectedText = item"
          >
            <div>
              <h3>{{ item.title }}</h3>
              <p>{{ item.summary }}</p>
            </div>
            <button type="button" title="删除" @click.stop="removeText(item.id)">×</button>
          </article>
        </div>
      </aside>

      <section class="main-grid">
        <section class="panel">
          <div class="panel-head">
            <h2>新增资料</h2>
          </div>
          <div class="form-grid">
            <label>
              标题
              <input v-model="newText.title" type="text" placeholder="例如：开源许可证概述" />
            </label>
            <label>
              关键词
              <input v-model="newText.keywords" type="text" placeholder="可留空，后端会自动提取" />
            </label>
            <label class="full">
              正文
              <textarea v-model="newText.content" rows="5" placeholder="粘贴或输入文本资料"></textarea>
            </label>
          </div>
          <div class="actions">
            <button type="button" class="primary" @click="addText">入库</button>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <h2>文件上传</h2>
          </div>
          <div class="upload-row">
            <input
              id="fileInput"
              type="file"
              accept=".txt,.md,.docx"
              @change="uploadFile = $event.target.files[0]"
            />
            <button type="button" @click="uploadSelectedFile">解析入库</button>
          </div>
        </section>

        <section class="panel document-panel">
          <div class="panel-head">
            <h2>生成文档</h2>
          </div>
          <div class="topic-row">
            <input v-model="topic" type="text" placeholder="输入文档主题" @keyup.enter="generateTree" />
            <button type="button" class="primary" @click="generateTree">生成结构树</button>
            <button type="button" @click="generateDocx">生成 Word</button>
          </div>
          <a v-if="downloadUrl" class="download" :href="downloadUrl">下载生成的 Word 文档</a>
          <pre class="tree-output">{{ treeJson || '结构树将在这里显示' }}</pre>
        </section>

        <section class="panel detail-panel">
          <div class="panel-head">
            <h2>资料详情</h2>
          </div>
          <div v-if="selectedText" class="detail">
            <h3>{{ selectedText.title }}</h3>
            <p class="meta">{{ selectedText.keywords }} · {{ selectedText.created_at }}</p>
            <p>{{ selectedText.content }}</p>
          </div>
          <p v-else class="empty">从左侧选择一条资料查看详情。</p>
        </section>
      </section>
    </section>
  </main>
</template>
