<script setup>
import { computed, onMounted, ref } from 'vue'

const API_BASE =
  import.meta.env.VITE_API_BASE ||
  (window.location.port === '5173' ? 'http://127.0.0.1:8000' : window.location.origin)

const tabs = [
  { key: 'library', label: '文本库选择', hint: '选择资料来源' },
  { key: 'template', label: '模板调节', hint: '控制生成风格' },
  { key: 'generate', label: '文档生成与预览', hint: '结构树与 Word' },
]

const libraries = ref([])

const templateSettings = ref({
  length: 70,
  professionalism: 80,
  formality: 75,
  structure: 85,
  evidence: 70,
  tables: 50,
  creativity: 40,
})
const templateConfigId = ref(null)
const templateConfigName = ref('默认模板配置')

const settingItems = [
  { key: 'length', label: '文本详细程度', minText: '简洁', maxText: '详细' },
  { key: 'professionalism', label: '专业程度', minText: '通俗', maxText: '专业' },
  { key: 'formality', label: '语言正式程度', minText: '自然', maxText: '正式' },
  { key: 'structure', label: '结构清晰程度', minText: '灵活', maxText: '清晰' },
  { key: 'evidence', label: '资料引用强度', minText: '弱引用', maxText: '强引用' },
  { key: 'tables', label: '表格使用程度', minText: '少表格', maxText: '多表格' },
  { key: 'creativity', label: '创新扩展程度', minText: '稳妥', maxText: '扩展' },
]

const activeTab = ref('library')
const texts = ref([])
const keyword = ref('')
const newText = ref({
  title: '',
  keywords: '',
  content: '',
})
const topic = ref('开源许可证分析报告')
const useLLM = ref(false)
const currentTree = ref(null)
const selectedText = ref(null)
const downloadUrl = ref('')
const notice = ref('')
const loading = ref(false)
const generatingWithLLM = ref(false)
const uploadFile = ref(null)
const feedbackText = ref('')
const showImprovementOptions = ref(false)
const improvementQuestion = ref('')
const improvementOptions = ref([])
const selectedImprovement = ref(null)

const treeJson = computed(() => (currentTree.value ? JSON.stringify(currentTree.value, null, 2) : ''))

const selectedLibraries = computed(() => libraries.value.filter((library) => library.checked))
const selectedLibraryIds = computed(() => selectedLibraries.value.map((library) => library.id))
const primaryLibraryId = computed(() => selectedLibraryIds.value[0] || libraries.value[0]?.id || null)

const templateSummary = computed(() => {
  const settings = templateSettings.value
  return {
    tendency: settings.length >= 60 ? '详细' : '简洁',
    style: settings.formality >= 65 ? '正式' : '自然',
    citation: settings.evidence >= 60 ? '强' : '弱',
    table: settings.tables >= 60 ? '多' : '少',
    clarity: settings.structure >= 70 ? '清晰' : '灵活',
  }
})

function setNotice(message) {
  notice.value = message
  window.clearTimeout(setNotice.timer)
  setNotice.timer = window.setTimeout(() => {
    notice.value = ''
  }, 3000)
}

function switchTab(tabKey) {
  activeTab.value = tabKey
}

function checkedLibraryChanged() {
  loadTexts()
}

function importMaterials() {
  const fileInput = document.querySelector('#fileInput')
  if (fileInput) {
    fileInput.click()
    setNotice('请选择文件后点击解析入库')
  }
}

function chooseImprovement(option) {
  selectedImprovement.value = option
  setNotice(`已选择：${option.label}`)
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || '请求失败')
  }
  return response.json()
}

async function loadLibraries() {
  const previousChecked = new Set(selectedLibraryIds.value)
  const rows = await apiFetch('/libraries')
  libraries.value = rows.map((library, index) => ({
    ...library,
    checked: previousChecked.size ? previousChecked.has(library.id) : index === 0,
  }))
}

async function loadTexts() {
  const selectedIds = selectedLibraryIds.value
  const keywordValue = keyword.value.trim().toLowerCase()
  if (selectedIds.length === 0) {
    texts.value = []
    return
  }
  if (selectedIds.length === 1) {
    const params = new URLSearchParams()
    if (keyword.value.trim()) params.set('keyword', keyword.value.trim())
    params.set('library_id', String(selectedIds[0]))
    texts.value = await apiFetch(`/texts?${params.toString()}`)
    return
  }
  const groupedTexts = await Promise.all(selectedIds.map((id) => apiFetch(`/libraries/${id}/texts`)))
  const merged = groupedTexts.flat()
  texts.value = keywordValue
    ? merged.filter((item) =>
        [item.title, item.summary, item.keywords, item.content]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(keywordValue)),
      )
    : merged
}

async function createLibrary() {
  const name = window.prompt('请输入新文本库名称')
  if (!name?.trim()) return
  const description = window.prompt('请输入文本库说明，可留空') || ''
  loading.value = true
  try {
    const created = await apiFetch('/libraries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name.trim(), description }),
    })
    await loadLibraries()
    libraries.value = libraries.value.map((library) => ({ ...library, checked: library.id === created.id }))
    await loadTexts()
    setNotice('文本库已创建')
  } catch (error) {
    setNotice(error.message)
  } finally {
    loading.value = false
  }
}

async function deleteSelectedLibrary() {
  if (selectedLibraries.value.length !== 1) {
    setNotice('请选择一个文本库后再删除')
    return
  }
  const library = selectedLibraries.value[0]
  if (!window.confirm(`确定删除“${library.name}”及其下所有资料吗？`)) return
  loading.value = true
  try {
    await apiFetch(`/libraries/${library.id}`, { method: 'DELETE' })
    await loadLibraries()
    await loadTexts()
    setNotice('文本库已删除')
  } catch (error) {
    setNotice(error.message)
  } finally {
    loading.value = false
  }
}

async function loadDefaultTemplateConfig() {
  const result = await apiFetch('/templates/configs/default')
  templateConfigId.value = result.id
  templateConfigName.value = result.name
  templateSettings.value = { ...templateSettings.value, ...result.config }
}

async function saveTemplateConfig() {
  loading.value = true
  try {
    if (templateConfigId.value) {
      const result = await apiFetch(`/templates/configs/${templateConfigId.value}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: templateConfigName.value || '默认模板配置',
          config: templateSettings.value,
          is_default: true,
        }),
      })
      templateSettings.value = { ...templateSettings.value, ...result.config }
    } else {
      const result = await apiFetch('/templates/configs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: templateConfigName.value || '默认模板配置',
          config: templateSettings.value,
          is_default: true,
        }),
      })
      templateConfigId.value = result.id
    }
    setNotice('模板配置已保存为默认')
  } catch (error) {
    setNotice(error.message)
  } finally {
    loading.value = false
  }
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
      body: JSON.stringify({ ...newText.value, library_id: primaryLibraryId.value }),
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
  if (primaryLibraryId.value) formData.append('library_id', String(primaryLibraryId.value))
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
    const fileInput = document.querySelector('#fileInput')
    if (fileInput) fileInput.value = ''
    await loadTexts()
    setNotice('文件已解析入库')
  } catch (error) {
    setNotice(error.message)
  } finally {
    loading.value = false
  }
}

async function generateTree() {
  if (!topic.value.trim()) {
    setNotice('请输入文档主题')
    return
  }
  loading.value = true
  generatingWithLLM.value = useLLM.value
  downloadUrl.value = ''
  activeTab.value = 'generate'
  try {
    const promptDelta = selectedImprovement.value?.prompt_delta || feedbackText.value.trim() || null
    currentTree.value = await apiFetch('/documents/tree', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topic.value.trim(),
        use_llm: useLLM.value,
        library_ids: selectedLibraryIds.value,
        template_config: templateSettings.value,
        prompt_delta: promptDelta,
      }),
    })
    setNotice('结构树已生成')
  } catch (error) {
    setNotice(error.message)
  } finally {
    loading.value = false
    generatingWithLLM.value = false
  }
}

async function generateImprovementOptions() {
  if (!currentTree.value) {
    setNotice('请先生成结构树，再生成反馈改进选项')
    return
  }
  if (!feedbackText.value.trim()) {
    setNotice('请先输入反馈内容')
    return
  }
  loading.value = true
  try {
    const result = await apiFetch('/documents/feedback-options', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topic.value.trim(),
        tree: currentTree.value,
        feedback: feedbackText.value.trim(),
      }),
    })
    improvementQuestion.value = result.question || '你希望如何改进当前文档？'
    improvementOptions.value = result.options || []
    selectedImprovement.value = null
    showImprovementOptions.value = true
    setNotice('反馈改进选项已生成')
  } catch (error) {
    setNotice(error.message)
  } finally {
    loading.value = false
  }
}

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

onMounted(async () => {
  try {
    await Promise.all([loadLibraries(), loadDefaultTemplateConfig()])
    await loadTexts()
  } catch (error) {
    setNotice(error.message)
  }
})
</script>

<template>
  <main class="app-shell">
    <header class="hero">
      <div class="brand-block">
        <p class="brand-mark">TextTreeDoc</p>
        <h1>文档结构树与 Word 自动生成工作台</h1>
        <p class="brand-subtitle">从文本库选择资料，调节生成风格，并快速导出课程报告文档。</p>
      </div>
      <div class="hero-status">
        <span class="metric">{{ texts.length }} 条资料</span>
        <span class="metric">{{ selectedLibraries.length }} 个文本库</span>
        <span class="status" :class="{ busy: loading }">{{ loading ? '处理中' : '就绪' }}</span>
      </div>
    </header>

    <nav class="tabbar" aria-label="主模块">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        class="tab-button"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        <span>{{ tab.label }}</span>
        <small>{{ tab.hint }}</small>
      </button>
    </nav>

    <p v-if="notice" class="notice">{{ notice }}</p>

    <section v-show="activeTab === 'library'" class="module-grid library-module">
      <aside class="panel library-selector">
        <div class="panel-head">
          <div>
            <p class="section-kicker">资料来源</p>
            <h2>文本库选择</h2>
          </div>
          <span class="soft-badge">后端已接入</span>
        </div>

        <div class="library-list">
          <label v-for="library in libraries" :key="library.id" class="library-card">
            <input v-model="library.checked" type="checkbox" @change="checkedLibraryChanged" />
            <span>
              <strong>{{ library.name }}</strong>
              <small>{{ library.count }} 条资料</small>
            </span>
          </label>
        </div>

        <div class="library-actions">
          <button type="button" class="ghost" @click="importMaterials">导入资料</button>
          <button type="button" class="ghost" :disabled="loading" @click="createLibrary">新建文本库</button>
          <button type="button" class="danger" :disabled="loading" @click="deleteSelectedLibrary">删除文本库</button>
        </div>
      </aside>

      <section class="panel source-panel">
        <div class="panel-head">
          <div>
            <p class="section-kicker">现有接口</p>
            <h2>资料列表</h2>
          </div>
          <button type="button" :disabled="loading" @click="loadTexts">刷新</button>
        </div>

        <div class="search-row">
          <input v-model="keyword" type="search" placeholder="搜索标题、关键词或正文" @keyup.enter="loadTexts" />
          <button type="button" :disabled="loading" @click="loadTexts">搜索</button>
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
              <div class="item-title-row">
                <h3>{{ item.title }}</h3>
                <span class="tag">{{ item.source_type || 'manual' }}</span>
              </div>
              <p>{{ item.summary || item.content }}</p>
            </div>
            <button type="button" title="删除" :disabled="loading" @click.stop="removeText(item.id)">删除</button>
          </article>
        </div>
      </section>

      <section class="panel entry-panel">
        <div class="panel-head">
          <div>
            <p class="section-kicker">手动构建</p>
            <h2>新增资料</h2>
          </div>
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
          <button type="button" class="primary" :disabled="loading" @click="addText">入库</button>
        </div>
      </section>

      <section class="panel upload-panel">
        <div class="panel-head">
          <div>
            <p class="section-kicker">批量导入</p>
            <h2>文件上传</h2>
          </div>
        </div>
        <div class="upload-row">
          <input
            id="fileInput"
            type="file"
            accept=".txt,.md,.docx"
            @change="uploadFile = $event.target.files[0]"
          />
          <button type="button" :disabled="loading" @click="uploadSelectedFile">解析入库</button>
        </div>
      </section>

      <section class="panel detail-panel">
        <div class="panel-head">
          <div>
            <p class="section-kicker">当前选中</p>
            <h2>资料详情</h2>
          </div>
        </div>
        <div v-if="selectedText" class="detail">
          <h3>{{ selectedText.title }}</h3>
          <p class="meta">{{ selectedText.keywords || '暂无关键词' }} · {{ selectedText.created_at }}</p>
          <p>{{ selectedText.content }}</p>
        </div>
        <p v-else class="empty">从资料列表中选择一条文本，详情会显示在这里。</p>
      </section>
    </section>

    <section v-show="activeTab === 'template'" class="module-grid template-module">
      <section class="panel tuner-panel">
        <div class="panel-head">
          <div>
            <p class="section-kicker">前端状态</p>
            <h2>模板参数调节器</h2>
          </div>
          <span class="soft-badge">后端已接入</span>
        </div>

        <div class="slider-list">
          <label v-for="setting in settingItems" :key="setting.key" class="slider-card">
            <span class="slider-title">
              <strong>{{ setting.label }}</strong>
              <em>{{ templateSettings[setting.key] }}</em>
            </span>
            <input v-model.number="templateSettings[setting.key]" type="range" min="1" max="100" />
            <span class="slider-scale">
              <small>{{ setting.minText }}</small>
              <small>{{ setting.maxText }}</small>
            </span>
          </label>
        </div>
        <div class="template-actions">
          <button type="button" class="ghost" :disabled="loading" @click="loadDefaultTemplateConfig">重新加载默认</button>
          <button type="button" class="primary" :disabled="loading" @click="saveTemplateConfig">保存为默认模板</button>
        </div>
      </section>

      <aside class="panel summary-panel">
        <div class="panel-head">
          <div>
            <p class="section-kicker">实时推断</p>
            <h2>当前模板摘要</h2>
          </div>
        </div>
        <div class="summary-card">
          <span>当前倾向</span>
          <strong>{{ templateSummary.tendency }}</strong>
        </div>
        <div class="summary-card">
          <span>风格</span>
          <strong>{{ templateSummary.style }}</strong>
        </div>
        <div class="summary-card">
          <span>资料引用</span>
          <strong>{{ templateSummary.citation }}</strong>
        </div>
        <div class="summary-card">
          <span>表格</span>
          <strong>{{ templateSummary.table }}</strong>
        </div>
        <p class="summary-note">
          当前结构更偏{{ templateSummary.clarity }}、{{ templateSummary.style }}的课程报告模板，
          适合先生成结构树，再根据反馈继续微调。
        </p>
      </aside>
    </section>

    <section v-show="activeTab === 'generate'" class="module-grid generate-module">
      <section class="panel generator-panel">
        <div class="panel-head">
          <div>
            <p class="section-kicker">结构树与 Word</p>
            <h2>文档生成</h2>
          </div>
          <span class="soft-badge">{{ selectedLibraries.length }} 个文本库已选</span>
        </div>

        <div class="topic-row">
          <input v-model="topic" type="text" placeholder="输入文档主题" @keyup.enter="generateTree" />
          <label class="switch">
            <input v-model="useLLM" type="checkbox" />
            使用 DeepSeek
          </label>
          <button type="button" class="primary" :disabled="loading" @click="generateTree">生成结构树</button>
          <button type="button" :disabled="loading || !currentTree" @click="generateDocx">生成 Word</button>
        </div>

        <a v-if="downloadUrl" class="download" :href="downloadUrl">下载生成的 Word 文档</a>

        <div class="feedback-box">
          <label>
            反馈改进
            <textarea
              v-model="feedbackText"
              rows="3"
              placeholder="例如“内容太短，希望更正式一些”"
            ></textarea>
          </label>
          <button type="button" class="ghost" :disabled="loading || !currentTree" @click="generateImprovementOptions">
            生成改进选项
          </button>
        </div>

        <div v-if="showImprovementOptions" class="improvement-list">
          <p class="improvement-question">{{ improvementQuestion }}</p>
          <button
            v-for="option in improvementOptions"
            :key="option.label"
            type="button"
            class="improvement-option"
            :class="{ selected: selectedImprovement?.label === option.label }"
            @click="chooseImprovement(option)"
          >
            <strong>{{ option.label }}</strong>
            <span>{{ option.description }}</span>
          </button>
        </div>
      </section>

      <section class="panel preview-panel">
        <div class="panel-head">
          <div>
            <p class="section-kicker">文档预览</p>
            <h2>结构树 JSON</h2>
          </div>
        </div>
        <div class="tree-frame">
          <div v-if="generatingWithLLM" class="loading-overlay">
            <span class="spinner"></span>
            <strong>DeepSeek 正在生成结构树</strong>
            <small>模型调用可能需要几秒，请稍候</small>
          </div>
          <pre class="tree-output">{{ treeJson || '结构树将在这里格式化展示。' }}</pre>
        </div>
      </section>
    </section>
  </main>
</template>
