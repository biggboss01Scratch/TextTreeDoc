<script setup>
import { computed, onMounted, ref } from 'vue'

const API_BASE =
  import.meta.env.VITE_API_BASE ||
  (/^517\d$/.test(window.location.port) ? 'http://127.0.0.1:8000' : window.location.origin)

const tabs = [
  { key: 'home', label: '首页', hint: '流程总览' },
  { key: 'library', label: '文本库', hint: '资料准备' },
  { key: 'documentTemplate', label: '格式', hint: 'Word 规范' },
  { key: 'structure', label: '结构树', hint: '目录骨架' },
  { key: 'images', label: '图片', hint: '插图位置' },
  { key: 'fill', label: '填充导出', hint: '正文与 Word' },
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
const documentTemplateTypes = ['实验报告', '结课论文', '技术分析报告', '项目设计文档']
const selectedDocumentTemplateType = ref('实验报告')
const documentTemplateRequirement = ref('正文首行缩进两个中文字符，1.5 倍行距，一级标题黑体三号，一级标题段前 18 磅段后 12 磅，正文宋体小四，标题编号使用 1 / 1.1 / 1.1.1。')
const formatDocumentText = ref('')
const formatDocumentFile = ref(null)
const formatAnalysis = ref(null)
const documentFormatConfig = ref({
  template_type: '实验报告',
  style_name: '实验报告模板',
  heading_numbering: 'decimal',
  cover: false,
  cover_style: 'none',
  toc: false,
  abstract: false,
  references: false,
  body_font: '宋体',
  heading_font: '黑体',
  ascii_font: 'Times New Roman',
  body_size: 12,
  heading1_size: 16,
  heading2_size: 14,
  heading3_size: 12,
  line_spacing: 1.5,
  line_spacing_rule: { type: 'multiple', value: 1.5, unit: 'line' },
  first_line_indent_chars: 2,
  paragraph_space_after: 6,
  body_space_before: { value: 0, unit: 'pt' },
  body_space_after: { value: 6, unit: 'pt' },
  heading1_space_before: { value: 18, unit: 'pt' },
  heading1_space_after: { value: 12, unit: 'pt' },
  heading2_space_before: { value: 12, unit: 'pt' },
  heading2_space_after: { value: 6, unit: 'pt' },
  heading3_space_before: { value: 6, unit: 'pt' },
  heading3_space_after: { value: 6, unit: 'pt' },
  table_style: 'Table Grid',
})

const activeTab = ref('home')
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
const toast = ref({
  message: '',
  type: 'success',
})
const loading = ref(false)
const generatingWithLLM = ref(false)
const fillingDocument = ref(false)
const buildingDocumentTemplate = ref(false)
const uploadFile = ref(null)
const imageUploadFile = ref(null)
const images = ref([])
const selectedImageId = ref(null)
const selectedSectionPath = ref('')
const showFormatJsonModal = ref(false)
const showTreeJsonModal = ref(false)
const feedbackText = ref('')
const showImprovementOptions = ref(false)
const improvementQuestion = ref('')
const improvementOptions = ref([])
const selectedImprovement = ref(null)

const treeJson = computed(() => (currentTree.value ? JSON.stringify(currentTree.value, null, 2) : ''))
const visualOutlineItems = computed(() => {
  if (!currentTree.value) return []
  const items = [{ id: 'root', depth: 0, path: '', title: currentTree.value.title || '未命名文档', type: 'title' }]
  flattenVisualSections(items, currentTree.value.sections || [], 1, [])
  return items
})
const sectionOptions = computed(() => visualOutlineItems.value.filter((item) => item.type === 'section'))
const selectedImage = computed(() => images.value.find((image) => image.id === selectedImageId.value) || null)

function flattenVisualSections(items, sections, depth, parentPath) {
  sections.forEach((section, index) => {
    const id = `${depth}-${index}-${section.heading || 'section'}`
    const path = [...parentPath, index]
    items.push({
      id,
      depth,
      path: path.join('.'),
      title: section.heading || '未命名章节',
      content: section.content || '',
      paragraphs: section.paragraphs || [],
      blocks: section.blocks || [],
      type: 'section',
    })
    flattenVisualSections(items, section.children || [], depth + 1, path)
  })
}

const selectedLibraries = computed(() => libraries.value.filter((library) => library.checked))
const selectedLibraryIds = computed(() => selectedLibraries.value.map((library) => library.id))
const primaryLibraryId = computed(() => selectedLibraryIds.value[0] || libraries.value[0]?.id || null)
const libraryReady = computed(() => selectedLibraries.value.length > 0 && texts.value.length > 0)
const formatReady = computed(() => Boolean(documentFormatConfig.value?.style_name))
const contentReady = computed(() => Boolean(topic.value.trim()))
const treeReady = computed(() => Boolean(currentTree.value))
const imageReady = computed(() => treeReady.value)
const filledParagraphCount = computed(() => countFilledParagraphs(currentTree.value?.sections || []))
const insertedImageCount = computed(() => countInsertedImages(currentTree.value?.sections || []))
const documentReady = computed(() => Boolean(downloadUrl.value))
const readyToGenerate = computed(() => libraryReady.value && formatReady.value && contentReady.value && treeReady.value)
const flowSteps = computed(() => [
  {
    key: 'library',
    number: 1,
    title: '文本库',
    desc: libraryReady.value ? `已选择 ${selectedLibraries.value.length} 个文本库，当前 ${texts.value.length} 条资料` : '选择或新建文本库，导入 txt、md、docx、PDF 资料。',
    ready: libraryReady.value,
    action: libraryReady.value ? '检查资料' : '去配置',
  },
  {
    key: 'documentTemplate',
    number: 2,
    title: '格式',
    desc: formatReady.value ? documentFormatSummary.value[0] : '选择报告类型，并让 AI 生成字体、行距、编号等 Word 格式。',
    ready: formatReady.value,
    action: formatReady.value ? '调整格式' : '去配置',
  },
  {
    key: 'structure',
    number: 3,
    title: '结构树',
    desc: treeReady.value ? `${sectionOptions.value.length} 个章节已生成` : contentReady.value ? `主题：${topic.value}` : '输入主题，先生成文档目录骨架。',
    ready: treeReady.value,
    action: treeReady.value ? '查看结构' : '生成结构',
  },
  {
    key: 'images',
    number: 4,
    title: '图片',
    desc: insertedImageCount.value ? `已插入 ${insertedImageCount.value} 张图片` : '把图片素材安排到结构树对应章节。',
    ready: imageReady.value,
    action: insertedImageCount.value ? '继续编排' : '去编排',
  },
  {
    key: 'fill',
    number: 5,
    title: '填充与导出',
    desc: documentReady.value ? 'Word 文档已生成' : filledParagraphCount.value ? `已填充 ${filledParagraphCount.value} 段正文` : '根据结构树、图片和文本库生成正文，最后导出 Word。',
    ready: documentReady.value,
    action: documentReady.value ? '下载' : '去完成',
  },
])
const nextStep = computed(() => flowSteps.value.find((step) => !step.ready) || flowSteps.value[4])

const documentFormatJson = computed(() => JSON.stringify(documentFormatConfig.value, null, 2))
const formatSpacingText = computed(() => {
  const config = documentFormatConfig.value
  return [
    `一级标题：段前 ${formatSpacing(config.heading1_space_before)}，段后 ${formatSpacing(config.heading1_space_after)}`,
    `二级标题：段前 ${formatSpacing(config.heading2_space_before)}，段后 ${formatSpacing(config.heading2_space_after)}`,
    `三级标题：段前 ${formatSpacing(config.heading3_space_before)}，段后 ${formatSpacing(config.heading3_space_after)}`,
    `正文：段前 ${formatSpacing(config.body_space_before)}，段后 ${formatSpacing(config.body_space_after)}`,
  ]
})
const documentFormatSummary = computed(() => {
  const config = documentFormatConfig.value
  return [
    `模板：${config.style_name || config.template_type}`,
    `编号：${config.heading_numbering === 'chinese' ? '一、（一）、1.' : '1 / 1.1 / 1.1.1'}`,
    `正文：${config.body_font} ${formatFontSize(config.body_size)}`,
    `标题：${config.heading_font} ${formatFontSize(config.heading1_size)} / ${formatFontSize(config.heading2_size)} / ${formatFontSize(config.heading3_size)}`,
    `行距：${formatLineSpacing(config)}`,
    `段落：首行缩进 ${config.first_line_indent_chars} 字`,
  ]
})

function formatFontSize(size) {
  const number = Number(size)
  const sizeMap = {
    42: '初号',
    36: '小初',
    26: '一号',
    24: '小一',
    22: '二号',
    18: '小二',
    16: '三号',
    15: '小三',
    14: '四号',
    12: '小四',
    10.5: '五号',
    9: '小五',
    7.5: '六号',
    6.5: '小六',
    5.5: '七号',
    5: '八号',
  }
  const label = sizeMap[number]
  return label ? `${label}（${number}pt）` : `${number}pt`
}

function formatSpacing(setting) {
  if (!setting || typeof setting !== 'object') return `${setting ?? 0}pt`
  const unitText = setting.unit === 'line' ? '行' : '磅'
  return `${setting.value}${unitText}`
}

function formatLineSpacing(config) {
  const rule = config.line_spacing_rule
  if (rule?.type === 'exact') return `固定 ${rule.value} 磅`
  return `${rule?.value || config.line_spacing} 倍`
}

function countFilledParagraphs(sections) {
  return sections.reduce((total, section) => {
    const own = Array.isArray(section.paragraphs) ? section.paragraphs.length : 0
    return total + own + countFilledParagraphs(section.children || [])
  }, 0)
}

function countInsertedImages(sections) {
  return sections.reduce((total, section) => {
    const own = (section.blocks || []).filter((block) => block.type === 'image').length
    return total + own + countInsertedImages(section.children || [])
  }, 0)
}

function setNotice(message, type = 'success') {
  toast.value = { message, type }
  window.clearTimeout(setNotice.timer)
  setNotice.timer = window.setTimeout(() => {
    toast.value = { message: '', type: 'success' }
  }, 3000)
}

function switchTab(tabKey) {
  activeTab.value = tabKey
}

async function runOneClickGenerate() {
  if (!libraryReady.value) {
    setNotice('请先配置文本库并导入资料', 'warning')
    activeTab.value = 'library'
    return
  }
  if (!formatReady.value) {
    setNotice('请先配置 Word 文档格式', 'warning')
    activeTab.value = 'documentTemplate'
    return
  }
  if (!contentReady.value) {
    setNotice('请先输入文档主题', 'warning')
    activeTab.value = 'structure'
    return
  }
  activeTab.value = 'structure'
  if (!currentTree.value) {
    await generateTree()
  }
  if (currentTree.value && filledParagraphCount.value === 0) {
    activeTab.value = 'fill'
    await fillDocumentContent()
  }
  if (currentTree.value && !downloadUrl.value) {
    activeTab.value = 'fill'
    await generateDocx()
  }
}

function checkedLibraryChanged() {
  loadTexts()
}

function importMaterials() {
  const fileInput = document.querySelector('#fileInput')
  if (fileInput) {
    fileInput.click()
  }
}

async function handleImportFile(event) {
  uploadFile.value = event.target.files?.[0] || null
  await uploadSelectedFile()
}

function importImages() {
  const imageInput = document.querySelector('#imageInput')
  if (imageInput) {
    imageInput.click()
  }
}

async function handleImageImport(event) {
  imageUploadFile.value = event.target.files?.[0] || null
  await uploadSelectedImage()
}

async function chooseImprovement(option) {
  selectedImprovement.value = option
  if (!topic.value.trim()) {
    setNotice('请输入文档主题', 'warning')
    return
  }
  loading.value = true
  generatingWithLLM.value = true
  downloadUrl.value = ''
  try {
    currentTree.value = await apiFetch('/documents/tree', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topic.value.trim(),
        use_llm: true,
        library_ids: selectedLibraryIds.value,
        template_config: {
          ...templateSettings.value,
          document_format: documentFormatConfig.value,
        },
        prompt_delta: option.prompt_delta,
      }),
    })
    setNotice(`已按“${option.label}”更新结构树`)
  } catch (error) {
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
    generatingWithLLM.value = false
  }
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '后端接口未返回有效 JSON，请确认后端服务已启动' }))
    throw new Error(error.detail || '请求失败')
  }
  return response.json().catch(() => {
    throw new Error('后端接口返回了非 JSON 内容，请检查 API 地址或后端服务')
  })
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

async function loadImages() {
  images.value = await apiFetch('/images')
  if (!selectedImageId.value && images.value.length) {
    selectedImageId.value = images.value[0].id
  }
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
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
  }
}

async function deleteSelectedLibrary() {
  if (selectedLibraries.value.length !== 1) {
    setNotice('请选择一个文本库后再删除', 'warning')
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
    setNotice(error.message, 'error')
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
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
  }
}

function applyDocumentTemplatePreset(type) {
  selectedDocumentTemplateType.value = type
  const presets = {
    实验报告: {
      template_type: '实验报告',
      style_name: '实验报告模板',
      heading_numbering: 'decimal',
      cover: false,
      cover_style: 'none',
      toc: false,
      abstract: false,
      references: false,
      line_spacing: 1.5,
      first_line_indent_chars: 2,
      table_style: 'Table Grid',
      body_space_before: { value: 0, unit: 'pt' },
      body_space_after: { value: 6, unit: 'pt' },
      heading1_space_before: { value: 18, unit: 'pt' },
      heading1_space_after: { value: 12, unit: 'pt' },
      heading2_space_before: { value: 12, unit: 'pt' },
      heading2_space_after: { value: 6, unit: 'pt' },
      heading3_space_before: { value: 6, unit: 'pt' },
      heading3_space_after: { value: 6, unit: 'pt' },
    },
    结课论文: {
      template_type: '结课论文',
      style_name: '结课论文模板',
      heading_numbering: 'chinese',
      cover: false,
      cover_style: 'none',
      toc: true,
      abstract: true,
      references: true,
      line_spacing: 1.5,
      first_line_indent_chars: 2,
      table_style: 'Table Grid',
      body_space_before: { value: 0, unit: 'pt' },
      body_space_after: { value: 6, unit: 'pt' },
      heading1_space_before: { value: 1, unit: 'line' },
      heading1_space_after: { value: 0.5, unit: 'line' },
      heading2_space_before: { value: 0.5, unit: 'line' },
      heading2_space_after: { value: 0.25, unit: 'line' },
      heading3_space_before: { value: 6, unit: 'pt' },
      heading3_space_after: { value: 6, unit: 'pt' },
    },
    技术分析报告: {
      template_type: '技术分析报告',
      style_name: '技术分析报告模板',
      heading_numbering: 'decimal',
      cover: false,
      cover_style: 'none',
      toc: true,
      abstract: false,
      references: true,
      line_spacing: 1.35,
      first_line_indent_chars: 2,
      table_style: 'Light Shading Accent 1',
      body_space_before: { value: 0, unit: 'pt' },
      body_space_after: { value: 6, unit: 'pt' },
      heading1_space_before: { value: 14, unit: 'pt' },
      heading1_space_after: { value: 8, unit: 'pt' },
      heading2_space_before: { value: 10, unit: 'pt' },
      heading2_space_after: { value: 6, unit: 'pt' },
      heading3_space_before: { value: 6, unit: 'pt' },
      heading3_space_after: { value: 4, unit: 'pt' },
    },
    项目设计文档: {
      template_type: '项目设计文档',
      style_name: '项目设计文档模板',
      heading_numbering: 'decimal',
      cover: false,
      cover_style: 'none',
      toc: true,
      abstract: false,
      references: false,
      line_spacing: 1.35,
      first_line_indent_chars: 0,
      table_style: 'Table Grid',
      body_space_before: { value: 0, unit: 'pt' },
      body_space_after: { value: 6, unit: 'pt' },
      heading1_space_before: { value: 1, unit: 'line' },
      heading1_space_after: { value: 0.5, unit: 'line' },
      heading2_space_before: { value: 0.5, unit: 'line' },
      heading2_space_after: { value: 0.25, unit: 'line' },
      heading3_space_before: { value: 6, unit: 'pt' },
      heading3_space_after: { value: 6, unit: 'pt' },
    },
  }
  documentFormatConfig.value = { ...documentFormatConfig.value, ...presets[type] }
}

async function buildDocumentTemplate() {
  loading.value = true
  buildingDocumentTemplate.value = useLLM.value
  try {
    documentFormatConfig.value = await apiFetch('/templates/configs/document-format', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        template_type: selectedDocumentTemplateType.value,
        requirement: documentTemplateRequirement.value,
        base_config: documentFormatConfig.value,
        use_llm: useLLM.value,
      }),
    })
    setNotice(useLLM.value ? 'AI 文档模板已生成' : '文档模板配置已生成')
  } catch (error) {
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
    buildingDocumentTemplate.value = false
  }
}

function importFormatDocument() {
  const input = document.querySelector('#formatDocumentInput')
  if (input) input.click()
}

async function handleFormatDocumentFile(event) {
  formatDocumentFile.value = event.target.files?.[0] || null
  await analyzeFormatFile()
}

async function analyzeFormatText() {
  if (!formatDocumentText.value.trim()) {
    setNotice('请先粘贴格式规范文本', 'warning')
    return
  }
  loading.value = true
  try {
    formatAnalysis.value = await apiFetch('/templates/configs/analyze-format-document', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: formatDocumentText.value,
        base_config: documentFormatConfig.value,
        use_llm: useLLM.value,
      }),
    })
    setNotice('格式规范已分析')
  } catch (error) {
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
  }
}

async function analyzeFormatFile() {
  if (!formatDocumentFile.value) {
    setNotice('请选择格式规范文件', 'warning')
    return
  }
  const formData = new FormData()
  formData.append('file', formatDocumentFile.value)
  formData.append('base_config_json', JSON.stringify(documentFormatConfig.value))
  formData.append('use_llm', String(useLLM.value))
  loading.value = true
  try {
    formatAnalysis.value = await fetch(`${API_BASE}/templates/configs/analyze-format-file`, {
      method: 'POST',
      body: formData,
    }).then(async (response) => {
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '格式规范文件分析失败' }))
        throw new Error(error.detail || '格式规范文件分析失败')
      }
      return response.json()
    })
    formatDocumentFile.value = null
    const input = document.querySelector('#formatDocumentInput')
    if (input) input.value = ''
    setNotice('格式规范文件已分析')
  } catch (error) {
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
  }
}

function applyFormatAnalysis() {
  if (!formatAnalysis.value?.format_config) {
    setNotice('请先分析格式规范', 'warning')
    return
  }
  documentFormatConfig.value = {
    ...documentFormatConfig.value,
    ...formatAnalysis.value.format_config,
  }
  setNotice('已应用格式规范分析结果')
}

async function addText() {
  if (!newText.value.title.trim() || !newText.value.content.trim()) {
    setNotice('请填写标题和正文', 'warning')
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
    setNotice(error.message, 'error')
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
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
  }
}

async function uploadSelectedFile() {
  if (!uploadFile.value) {
    setNotice('请选择文件', 'warning')
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
        const error = await response.json().catch(() => ({ detail: '上传失败，请确认后端服务已启动并支持该文件类型' }))
        throw new Error(error.detail || '上传失败')
      }
      return response.json().catch(() => {
        throw new Error('上传接口返回了非 JSON 内容，请检查 API 地址或后端服务')
      })
    })
    uploadFile.value = null
    const fileInput = document.querySelector('#fileInput')
    if (fileInput) fileInput.value = ''
    await loadTexts()
    setNotice('文件已解析入库')
  } catch (error) {
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
  }
}

async function uploadSelectedImage() {
  if (!imageUploadFile.value) {
    setNotice('请选择图片', 'warning')
    return
  }
  const formData = new FormData()
  formData.append('file', imageUploadFile.value)
  formData.append('name', imageUploadFile.value.name.replace(/\.[^.]+$/, ''))
  loading.value = true
  try {
    const created = await fetch(`${API_BASE}/images`, {
      method: 'POST',
      body: formData,
    }).then(async (response) => {
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '图片上传失败' }))
        throw new Error(error.detail || '图片上传失败')
      }
      return response.json()
    })
    imageUploadFile.value = null
    const imageInput = document.querySelector('#imageInput')
    if (imageInput) imageInput.value = ''
    await loadImages()
    selectedImageId.value = created.id
    setNotice('图片已加入素材库')
  } catch (error) {
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
  }
}

async function updateImageMeta(image) {
  loading.value = true
  try {
    const updated = await apiFetch(`/images/${image.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: image.name,
        caption: image.caption,
        description: image.description,
      }),
    })
    images.value = images.value.map((item) => (item.id === updated.id ? updated : item))
    setNotice('图片信息已保存')
  } catch (error) {
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
  }
}

function autoGenerateCaption(image, index) {
  const title = normalizeImageTitle(image.name || `图片 ${index + 1}`)
  const order = index >= 0 ? index + 1 : images.value.findIndex((item) => item.id === image.id) + 1
  image.caption = `图 ${Math.max(order, 1)} ${title}`
}

async function removeImage(imageId) {
  if (!window.confirm('确定删除这张图片素材吗？')) return
  loading.value = true
  try {
    await apiFetch(`/images/${imageId}`, { method: 'DELETE' })
    images.value = images.value.filter((image) => image.id !== imageId)
    if (selectedImageId.value === imageId) selectedImageId.value = images.value[0]?.id || null
    setNotice('图片已删除')
  } catch (error) {
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
  }
}

function insertSelectedImage() {
  if (!currentTree.value) {
    setNotice('请先生成结构树', 'warning')
    activeTab.value = 'structure'
    return
  }
  if (!selectedImage.value) {
    setNotice('请先上传或选择图片', 'warning')
    return
  }
  if (!selectedSectionPath.value) {
    setNotice('请选择要插入图片的章节', 'warning')
    return
  }
  const tree = JSON.parse(JSON.stringify(currentTree.value))
  const section = getSectionByPath(tree, selectedSectionPath.value)
  if (!section) {
    setNotice('章节不存在，请重新选择', 'error')
    return
  }
  const image = selectedImage.value
  section.blocks = section.blocks || []
  const caption = buildSectionImageCaption(section, image)
  section.blocks.push({
    type: 'image',
    image_id: image.id,
    title: image.name,
    caption,
    description: image.description || '',
  })
  currentTree.value = tree
  setNotice(`已插入图片“${caption}”`)
}

function removeImageBlock(path, blockIndex) {
  const tree = JSON.parse(JSON.stringify(currentTree.value))
  const section = getSectionByPath(tree, path)
  if (!section?.blocks) return
  section.blocks.splice(blockIndex, 1)
  currentTree.value = tree
  setNotice('已从结构树移除图片')
}

function getSectionByPath(tree, path) {
  const indexes = path.split('.').filter(Boolean).map((value) => Number(value))
  let sections = tree.sections || []
  let section = null
  for (const index of indexes) {
    section = sections[index]
    if (!section) return null
    sections = section.children || []
  }
  return section
}

function buildSectionImageCaption(section, image) {
  const headingNumber = extractHeadingNumber(section.heading || '')
  const title = normalizeImageTitle(image.name || image.caption || '图片')
  const existingImageCount = (section.blocks || []).filter((block) => block.type === 'image').length
  if (!headingNumber) {
    return `图 ${existingImageCount + 1} ${title}`
  }
  const number = existingImageCount > 0 ? `${headingNumber}-${existingImageCount + 1}` : headingNumber
  return `图 ${number} ${title}`
}

function extractHeadingNumber(heading) {
  const decimalMatch = String(heading).trim().match(/^(\d+(?:\.\d+)*)/)
  if (decimalMatch) return decimalMatch[1]
  const chineseMatch = String(heading).trim().match(/^([一二三四五六七八九十]+)、/)
  if (chineseMatch) return chineseMatch[1]
  return ''
}

function normalizeImageTitle(title) {
  return String(title || '图片')
    .replace(/^图\s*[\d一二三四五六七八九十]+(?:[.\-]\d+)*[：:\s]*/, '')
    .trim() || '图片'
}

async function generateTree() {
  if (!topic.value.trim()) {
    setNotice('请输入文档主题', 'warning')
    return
  }
  loading.value = true
  generatingWithLLM.value = useLLM.value
  downloadUrl.value = ''
  activeTab.value = 'structure'
  try {
    const promptDelta = selectedImprovement.value?.prompt_delta || feedbackText.value.trim() || null
    currentTree.value = await apiFetch('/documents/tree', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topic.value.trim(),
        use_llm: useLLM.value,
        library_ids: selectedLibraryIds.value,
        template_config: {
          ...templateSettings.value,
          document_format: documentFormatConfig.value,
        },
        prompt_delta: promptDelta,
      }),
    })
    selectedSectionPath.value = sectionOptions.value[0]?.path || ''
    downloadUrl.value = ''
    setNotice('结构树已生成')
  } catch (error) {
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
    generatingWithLLM.value = false
  }
}

async function fillDocumentContent() {
  if (!currentTree.value) {
    setNotice('请先生成结构树', 'warning')
    return
  }
  if (!topic.value.trim()) {
    setNotice('请输入文档主题', 'warning')
    return
  }
  loading.value = true
  fillingDocument.value = useLLM.value
  downloadUrl.value = ''
  activeTab.value = 'fill'
  try {
    currentTree.value = await apiFetch('/documents/fill', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topic.value.trim(),
        tree: currentTree.value,
        use_llm: useLLM.value,
        library_ids: selectedLibraryIds.value,
        template_config: {
          ...templateSettings.value,
          document_format: documentFormatConfig.value,
        },
      }),
    })
    setNotice(useLLM.value ? 'AI 正文已填充' : '正文已填充')
  } catch (error) {
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
    fillingDocument.value = false
  }
}

async function generateImprovementOptions() {
  if (!currentTree.value) {
    setNotice('请先生成结构树，再生成反馈改进选项', 'warning')
    return
  }
  if (!feedbackText.value.trim()) {
    setNotice('请先输入反馈内容', 'warning')
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
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
  }
}

async function generateDocx() {
  if (!currentTree.value) {
    setNotice('请先生成文档结构树', 'warning')
    return
  }
  loading.value = true
  try {
    const result = await apiFetch('/documents/docx', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: currentTree.value.title,
        tree: currentTree.value,
        format_config: documentFormatConfig.value,
      }),
    })
    downloadUrl.value = `${API_BASE}${result.download_url}`
    setNotice('Word 文档已生成')
  } catch (error) {
    setNotice(error.message, 'error')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    await Promise.all([loadLibraries(), loadDefaultTemplateConfig(), loadImages()])
    await loadTexts()
  } catch (error) {
    setNotice(error.message, 'error')
  }
})
</script>

<template>
  <a class="skip-link" href="#main-content">跳到主要内容</a>
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

    <Transition name="toast">
      <div v-if="toast.message" class="toast" :class="`toast-${toast.type}`" role="status">
        <span class="toast-dot"></span>
        <span>{{ toast.message }}</span>
      </div>
    </Transition>

    <div id="main-content" class="page-stage">
      <section v-show="activeTab === 'home'" class="home-module page-panel">
        <section class="home-hero-panel">
          <div>
            <p class="section-kicker">流程式文档生成</p>
            <h2>按文本库、格式、结构树、图片、正文五步生成报告</h2>
            <p>
              先准备资料，再确定 Word 规范；结构树只负责目录骨架，图片单独编排，最后再填充正文并导出文档。
              每一步都可以返工调整。
            </p>
          </div>
          <div class="home-actions">
            <button type="button" class="primary hero-action" :disabled="loading" @click="runOneClickGenerate">
              一键生成文档
            </button>
            <button type="button" class="ghost" @click="switchTab(nextStep.key)">
              继续：{{ nextStep.title }}
            </button>
          </div>
        </section>

        <section class="flow-chain" aria-label="生成流程">
          <button
            v-for="step in flowSteps"
            :key="step.key"
            type="button"
            class="flow-step"
            :class="{ ready: step.ready, current: activeTab === step.key || nextStep.key === step.key }"
            @click="switchTab(step.key)"
          >
            <span class="step-number">{{ step.number }}</span>
            <span class="step-body">
              <strong>{{ step.title }}</strong>
              <small>{{ step.desc }}</small>
            </span>
            <span class="step-action">{{ step.action }}</span>
          </button>
        </section>

        <section class="home-dashboard">
          <article class="panel readiness-panel">
            <div class="panel-head">
              <div>
                <p class="section-kicker">当前状态</p>
                <h2>{{ readyToGenerate ? '可以生成' : '还需配置' }}</h2>
              </div>
              <span class="status" :class="{ busy: loading }">{{ loading ? '处理中' : readyToGenerate ? '已就绪' : '待完善' }}</span>
            </div>
            <div class="readiness-list">
              <span :class="{ done: libraryReady }">资料：{{ libraryReady ? `${texts.length} 条可用` : '未完成' }}</span>
              <span :class="{ done: formatReady }">格式：{{ formatReady ? documentFormatConfig.style_name : '未完成' }}</span>
              <span :class="{ done: contentReady }">主题：{{ contentReady ? topic : '未填写' }}</span>
            </div>
          </article>

          <article class="panel quick-panel">
            <div class="panel-head">
              <div>
                <p class="section-kicker">快捷入口</p>
                <h2>常用操作</h2>
              </div>
            </div>
            <div class="quick-actions">
              <button type="button" class="ghost" @click="switchTab('library')">导入或选择资料</button>
              <button type="button" class="ghost" @click="switchTab('documentTemplate')">生成格式模板</button>
              <button type="button" class="ghost" @click="switchTab('structure')">生成结构树</button>
              <button type="button" class="ghost" @click="switchTab('fill')">填充并导出</button>
            </div>
          </article>
        </section>
      </section>

      <section v-show="activeTab === 'library'" class="module-grid library-module page-panel">
      <aside class="panel library-selector">
        <div class="panel-head">
          <div>
            <p class="section-kicker">资料来源</p>
            <h2>文本库选择</h2>
          </div>
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
        <input
          id="fileInput"
          class="hidden-file-input"
          type="file"
          accept=".txt,.md,.docx,.pdf"
          @change="handleImportFile"
        />
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
          <div v-if="texts.length === 0" class="empty-state">
            <strong>还没有可用资料</strong>
            <span>导入 txt、md、docx 或文字型 PDF，或在右侧手动新增资料。</span>
          </div>
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

    <section v-show="activeTab === 'documentTemplate'" class="module-grid document-template-module page-panel">
      <section class="panel format-builder-panel">
        <div v-if="buildingDocumentTemplate" class="loading-overlay light-loading-overlay">
          <span class="spinner"></span>
          <strong>DeepSeek 正在生成文档格式模板</strong>
          <small>正在分析标题编号、字体、行距和段落格式</small>
        </div>
        <div class="panel-head">
          <div>
            <p class="section-kicker">Word 格式模板</p>
            <h2>AI 文档模板构建</h2>
          </div>
          <span class="soft-badge">{{ selectedDocumentTemplateType }}</span>
        </div>

        <div class="template-type-grid">
          <button
            v-for="type in documentTemplateTypes"
            :key="type"
            type="button"
            class="template-type-card"
            :class="{ active: selectedDocumentTemplateType === type }"
            @click="applyDocumentTemplatePreset(type)"
          >
            <strong>{{ type }}</strong>
            <span>{{ type === '结课论文' ? '摘要、目录、参考文献' : type === '实验报告' ? '过程、结果、表格' : type === '技术分析报告' ? '分析、对比、引用' : '模块、接口、设计说明' }}</span>
          </button>
        </div>

        <label class="format-requirement">
          向 AI 描述格式要求
          <textarea
            v-model="documentTemplateRequirement"
            rows="6"
            placeholder="例如：正文首行缩进两个中文字符，1.5 倍行距，一级标题黑体三号，一级标题段前 18 磅段后 12 磅，二级标题段前 0.5 行段后 6 磅，正文宋体小四。"
          ></textarea>
        </label>

        <section class="format-document-box">
          <div class="panel-head compact-head">
            <div>
              <p class="section-kicker">格式规范文档</p>
              <h3>上传或粘贴规范，自动抽取格式</h3>
            </div>
            <button type="button" class="ghost" :disabled="loading" @click="importFormatDocument">上传规范</button>
          </div>
          <input
            id="formatDocumentInput"
            class="hidden-file-input"
            type="file"
            accept=".txt,.md,.docx,.pdf"
            @change="handleFormatDocumentFile"
          />
          <textarea
            v-model="formatDocumentText"
            rows="4"
            placeholder="也可以直接粘贴格式规范文本，例如封面、摘要、目录、标题字号、正文行距、表题图题等要求。"
          ></textarea>
          <div class="format-doc-actions">
            <button type="button" class="ghost" :disabled="loading" @click="analyzeFormatText">分析粘贴文本</button>
            <button type="button" class="primary" :disabled="loading || !formatAnalysis" @click="applyFormatAnalysis">
              应用分析结果
            </button>
          </div>
        </section>

        <div class="format-actions">
          <label class="switch compact-switch">
            <input v-model="useLLM" type="checkbox" class="switch-native" />
            <span class="switch-box"></span>
            <span class="switch-text">使用 DeepSeek 生成格式</span>
          </label>
          <button type="button" class="primary" :disabled="loading" @click="buildDocumentTemplate">
            生成文档模板配置
          </button>
        </div>
      </section>

      <aside class="panel format-preview-panel">
        <div class="panel-head">
          <div>
            <p class="section-kicker">格式结果</p>
            <h2>{{ documentFormatConfig.style_name }}</h2>
          </div>
          <button type="button" class="ghost" @click="showFormatJsonModal = true">查看 JSON</button>
        </div>
        <div class="format-chip-grid">
          <span v-for="item in documentFormatSummary" :key="item" class="format-chip">{{ item }}</span>
          <span class="format-chip">封面：{{ documentFormatConfig.cover ? '需要' : '不需要' }}</span>
          <span v-if="documentFormatConfig.cover" class="format-chip">
            封面样式：{{ documentFormatConfig.cover_style === 'wuhan_cs_course_design' ? '武汉计院课程设计' : '简易/未指定' }}
          </span>
          <span class="format-chip">目录：{{ documentFormatConfig.toc ? '需要' : '不需要' }}</span>
          <span class="format-chip">摘要：{{ documentFormatConfig.abstract ? '需要' : '不需要' }}</span>
          <span class="format-chip">参考文献：{{ documentFormatConfig.references ? '需要' : '不需要' }}</span>
          <span v-for="item in formatSpacingText" :key="item" class="format-chip wide-chip">{{ item }}</span>
          <span v-if="documentFormatConfig.line_spacing_rule?.type === 'exact'" class="format-chip wide-chip">
            固定行距：{{ documentFormatConfig.line_spacing_rule.value }} 磅
          </span>
        </div>
        <div v-if="formatAnalysis" class="format-analysis-card">
          <h3>规范分析结果</h3>
          <div class="format-chip-grid">
            <span v-for="rule in formatAnalysis.extracted_rules" :key="rule" class="format-chip">{{ rule }}</span>
            <span v-for="item in formatAnalysis.structure_requirements" :key="item.key" class="format-chip">
              结构：{{ item.label }}
            </span>
            <span v-for="field in formatAnalysis.metadata_fields" :key="field.key" class="format-chip">
              字段：{{ field.label }}
            </span>
          </div>
          <p v-for="warning in formatAnalysis.warnings" :key="warning" class="analysis-warning">{{ warning }}</p>
        </div>
        <div class="format-visual-card">
          <span class="paper-line title-line"></span>
          <span class="paper-line heading-line"></span>
          <span class="paper-line body-line"></span>
          <span class="paper-line body-line short"></span>
          <span class="paper-table-preview"></span>
        </div>
      </aside>
    </section>

    <section v-show="activeTab === 'structure'" class="module-grid structure-module page-panel">
      <section class="panel generator-panel">
        <div class="panel-head">
          <div>
            <p class="section-kicker">目录骨架</p>
            <h2>生成结构树</h2>
          </div>
          <span class="soft-badge">{{ selectedLibraries.length }} 个文本库已选</span>
        </div>

        <div class="structure-action-row">
          <input v-model="topic" type="text" placeholder="输入文档主题" @keyup.enter="generateTree" />
          <label class="switch">
            <input v-model="useLLM" type="checkbox" class="switch-native" />
            <span class="switch-box"></span>
            <span class="switch-text">使用 DeepSeek</span>
          </label>
          <button type="button" class="primary" :disabled="loading" @click="generateTree">生成结构树</button>
        </div>

        <div class="result-toolbar">
          <span class="result-hint">
            {{ currentTree ? `已生成 ${sectionOptions.length} 个章节，下一步可以编排图片` : '结构树生成后会保留在当前流程中' }}
          </span>
          <button type="button" class="ghost" :disabled="!currentTree" @click="switchTab('images')">下一步：图片</button>
          <button type="button" class="ghost" :disabled="!currentTree" @click="showTreeJsonModal = true">查看 JSON</button>
        </div>

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
            <h2>图形化目录树</h2>
          </div>
        </div>
        <div class="tree-frame">
          <div v-if="generatingWithLLM || fillingDocument" class="loading-overlay">
            <span class="spinner"></span>
            <strong>{{ fillingDocument ? 'DeepSeek 正在填充正文' : 'DeepSeek 正在生成结构树' }}</strong>
            <small>{{ fillingDocument ? '正在根据结构树、图片和文本库生成正文段落' : '模型调用可能需要几秒，请稍候' }}</small>
          </div>
          <div v-if="visualOutlineItems.length" class="visual-tree">
            <article
              v-for="item in visualOutlineItems"
              :key="item.id"
              class="visual-tree-item"
              :class="`depth-${Math.min(item.depth, 4)}`"
            >
              <span class="tree-node-dot"></span>
              <div>
                <strong>{{ item.title }}</strong>
                <p v-if="item.content">{{ item.content.slice(0, 80) }}{{ item.content.length > 80 ? '...' : '' }}</p>
                <div v-if="item.paragraphs?.length" class="tree-paragraph-count">
                  已填充 {{ item.paragraphs.length }} 段正文
                </div>
                <div v-if="item.blocks?.length" class="tree-block-tags">
                  <span v-for="(block, index) in item.blocks" :key="index">
                    {{ block.type === 'table' ? '表格' : block.type || '内容块' }}
                  </span>
                </div>
              </div>
            </article>
          </div>
          <div v-else class="empty-state tree-empty">
            <strong>还没有结构树</strong>
            <span>生成结构树后，这里会展示图形化目录。</span>
          </div>
        </div>
      </section>
    </section>

    <section v-show="activeTab === 'images'" class="module-grid image-module page-panel">
      <aside class="panel image-library-panel">
        <div class="panel-head">
          <div>
            <p class="section-kicker">图片素材</p>
            <h2>图片库</h2>
          </div>
          <button type="button" class="ghost" :disabled="loading" @click="importImages">上传图片</button>
        </div>
        <input
          id="imageInput"
          class="hidden-file-input"
          type="file"
          accept=".png,.jpg,.jpeg"
          @change="handleImageImport"
        />
        <div class="image-list">
          <article
            v-for="(image, index) in images"
            :key="image.id"
            class="image-card"
            :class="{ active: selectedImageId === image.id }"
            @click="selectedImageId = image.id"
          >
            <img :src="`${API_BASE}${image.preview_url}`" :alt="image.name" />
            <div class="image-card-copy">
              <strong>{{ image.name }}</strong>
              <span>{{ image.caption || `图 ${index + 1}` }}</span>
              <small>{{ image.description || '暂无说明' }}</small>
            </div>
          </article>
          <div v-if="images.length === 0" class="empty-state">
            <strong>还没有图片素材</strong>
            <span>上传 png、jpg 或 jpeg 图片后，可以插入到结构树章节里。</span>
          </div>
        </div>
      </aside>

      <section class="panel image-arrange-panel">
        <div class="panel-head">
          <div>
            <p class="section-kicker">结构树插图</p>
            <h2>图片编排</h2>
          </div>
          <span class="soft-badge">{{ visualOutlineItems.length ? `${sectionOptions.length} 个章节` : '未生成结构树' }}</span>
        </div>

        <section v-if="selectedImage" class="selected-image-panel">
          <img :src="`${API_BASE}${selectedImage.preview_url}`" :alt="selectedImage.name" />
          <div class="selected-image-form">
            <label>
              图片名称
              <input v-model="selectedImage.name" type="text" placeholder="图片名称" />
            </label>
            <label>
              Word 图注
              <input v-model="selectedImage.caption" type="text" placeholder="例如：图 2.1 系统架构图" />
            </label>
            <label>
              图片说明
              <textarea v-model="selectedImage.description" rows="2" placeholder="图片说明，可用于后续 AI 推荐"></textarea>
            </label>
            <div class="selected-image-actions">
              <button type="button" class="ghost" @click.stop="autoGenerateCaption(selectedImage, images.findIndex((item) => item.id === selectedImage.id))">
                自动图注
              </button>
              <button type="button" class="ghost" :disabled="loading" @click.stop="updateImageMeta(selectedImage)">保存信息</button>
              <button type="button" class="danger" :disabled="loading" @click.stop="removeImage(selectedImage.id)">删除</button>
            </div>
          </div>
        </section>

        <div class="image-insert-row">
          <label>
            插入章节
            <select v-model="selectedSectionPath" :disabled="!currentTree">
              <option value="">选择章节</option>
              <option v-for="section in sectionOptions" :key="section.path" :value="section.path">
                {{ '　'.repeat(Math.max(section.depth - 1, 0)) }}{{ section.title }}
              </option>
            </select>
          </label>
          <button type="button" class="primary" :disabled="loading || !currentTree || !selectedImage" @click="insertSelectedImage">
            插入到章节
          </button>
          <button type="button" class="ghost" :disabled="!currentTree" @click="switchTab('fill')">下一步：填充</button>
        </div>

        <div v-if="visualOutlineItems.length" class="visual-tree image-tree">
          <article
            v-for="item in visualOutlineItems"
            :key="item.id"
            class="visual-tree-item"
            :class="[`depth-${Math.min(item.depth, 4)}`, { selected: selectedSectionPath === item.path && item.type === 'section' }]"
            @click="item.type === 'section' ? (selectedSectionPath = item.path) : null"
          >
            <span class="tree-node-dot"></span>
            <div>
              <strong>{{ item.title }}</strong>
              <p v-if="item.content">{{ item.content.slice(0, 80) }}{{ item.content.length > 80 ? '...' : '' }}</p>
              <div v-if="item.blocks?.length" class="tree-block-tags">
                <span v-for="(block, index) in item.blocks" :key="index">
                  {{ block.type === 'image' ? `图片：${block.caption || block.title || block.image_id}` : block.type === 'table' ? '表格' : block.type || '内容块' }}
                  <button
                    v-if="block.type === 'image'"
                    type="button"
                    title="移除图片"
                    @click.stop="removeImageBlock(item.path, index)"
                  >
                    移除
                  </button>
                </span>
              </div>
            </div>
          </article>
        </div>
        <div v-else class="empty-state tree-empty">
          <strong>请先生成结构树</strong>
          <span>生成结构树后，可以把图片插入到指定章节。</span>
        </div>
      </section>
    </section>

    <section v-show="activeTab === 'fill'" class="module-grid fill-module page-panel">
      <section class="panel generator-panel">
        <div class="panel-head">
          <div>
            <p class="section-kicker">正文与 Word</p>
            <h2>填充内容并导出</h2>
          </div>
          <span class="soft-badge">{{ filledParagraphCount ? `已填充 ${filledParagraphCount} 段` : '等待填充' }}</span>
        </div>

        <div class="fill-status-grid">
          <span :class="{ done: currentTree }">结构树：{{ currentTree ? `${sectionOptions.length} 个章节` : '未生成' }}</span>
          <span :class="{ done: insertedImageCount > 0 }">图片：{{ insertedImageCount ? `${insertedImageCount} 张已插入` : '可选' }}</span>
          <span :class="{ done: filledParagraphCount > 0 }">正文：{{ filledParagraphCount ? `${filledParagraphCount} 段` : '未填充' }}</span>
          <span :class="{ done: downloadUrl }">Word：{{ downloadUrl ? '已生成' : '未生成' }}</span>
        </div>

        <div class="fill-action-row">
          <label class="switch">
            <input v-model="useLLM" type="checkbox" class="switch-native" />
            <span class="switch-box"></span>
            <span class="switch-text">使用 DeepSeek</span>
          </label>
          <button type="button" class="primary" :disabled="loading || !currentTree" @click="fillDocumentContent">填充正文</button>
          <button type="button" :disabled="loading || !currentTree" @click="generateDocx">生成 Word</button>
          <a v-if="downloadUrl" class="download" :href="downloadUrl">下载 Word</a>
          <button v-else type="button" class="ghost" disabled>等待导出</button>
        </div>

        <div class="result-toolbar">
          <button type="button" class="ghost" :disabled="!currentTree" @click="switchTab('structure')">返回结构树</button>
          <button type="button" class="ghost" :disabled="!currentTree" @click="switchTab('images')">调整图片</button>
          <button type="button" class="ghost" :disabled="!currentTree" @click="showTreeJsonModal = true">查看 JSON</button>
        </div>
      </section>

      <section class="panel preview-panel">
        <div class="panel-head">
          <div>
            <p class="section-kicker">最终预览</p>
            <h2>正文填充状态</h2>
          </div>
        </div>
        <div class="tree-frame">
          <div v-if="fillingDocument" class="loading-overlay">
            <span class="spinner"></span>
            <strong>DeepSeek 正在填充正文</strong>
            <small>正在根据结构树、图片和文本库生成正文段落</small>
          </div>
          <div v-if="visualOutlineItems.length" class="visual-tree">
            <article
              v-for="item in visualOutlineItems"
              :key="item.id"
              class="visual-tree-item"
              :class="`depth-${Math.min(item.depth, 4)}`"
            >
              <span class="tree-node-dot"></span>
              <div>
                <strong>{{ item.title }}</strong>
                <p v-if="item.content">{{ item.content.slice(0, 80) }}{{ item.content.length > 80 ? '...' : '' }}</p>
                <div v-if="item.paragraphs?.length" class="tree-paragraph-count">
                  已填充 {{ item.paragraphs.length }} 段正文
                </div>
                <div v-if="item.blocks?.length" class="tree-block-tags">
                  <span v-for="(block, index) in item.blocks" :key="index">
                    {{ block.type === 'image' ? `图片：${block.caption || block.title || block.image_id}` : block.type === 'table' ? '表格' : block.type || '内容块' }}
                  </span>
                </div>
              </div>
            </article>
          </div>
          <div v-else class="empty-state tree-empty">
            <strong>还没有可填充的结构树</strong>
            <span>请先完成结构树生成。</span>
          </div>
        </div>
      </section>
    </section>

    <Teleport to="body">
      <div v-if="showFormatJsonModal" class="modal-backdrop" @click.self="showFormatJsonModal = false">
        <section class="json-modal" role="dialog" aria-modal="true" aria-label="文档格式 JSON">
          <header class="modal-head">
            <div>
              <p class="section-kicker">原始配置</p>
              <h2>文档格式 JSON</h2>
            </div>
            <button type="button" class="ghost" @click="showFormatJsonModal = false">关闭</button>
          </header>
          <pre class="json-modal-body">{{ documentFormatJson }}</pre>
        </section>
      </div>
      <div v-if="showTreeJsonModal" class="modal-backdrop" @click.self="showTreeJsonModal = false">
        <section class="json-modal" role="dialog" aria-modal="true" aria-label="结构树 JSON">
          <header class="modal-head">
            <div>
              <p class="section-kicker">原始结构</p>
              <h2>结构树 JSON</h2>
            </div>
            <button type="button" class="ghost" @click="showTreeJsonModal = false">关闭</button>
          </header>
          <pre class="json-modal-body">{{ treeJson || '暂无结构树 JSON' }}</pre>
        </section>
      </div>
    </Teleport>
    </div>
  </main>
</template>
