<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Settings', to: '/dashboard/settings' },
      { label: 'AI Providers' }
    ]" />

    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">AI Providers</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
        Configure API keys and settings for AI integrations used across the application.
      </p>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 animate-spin text-gray-400" />
    </div>

    <div v-else class="space-y-6">
      <UCard v-for="provider in providers" :key="provider.provider">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center"
                :class="providerIconBg(provider.provider)">
                <UIcon :name="providerIcon(provider.provider)" class="w-5 h-5"
                  :class="providerIconColor(provider.provider)" />
              </div>
              <div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ provider.display_name }}</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ provider.provider }}</p>
              </div>
            </div>
            <UBadge
              :color="statusColor(provider)"
              variant="subtle"
              size="sm"
            >
              {{ statusLabel(provider) }}
            </UBadge>
          </div>
        </template>

        <div class="space-y-4">
          <!-- API Key -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">API Key</label>
            <UInput
              v-model="forms[provider.provider].api_key"
              type="password"
              :placeholder="provider.has_api_key ? 'Key configured (enter new key to change)' : 'Enter API key'"
            />
          </div>

          <!-- Default Model -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Default Model</label>
            <USelect
              v-model="forms[provider.provider].default_model"
              :items="modelOptions[provider.provider] || []"
            />
          </div>

          <!-- Base URL (shown for DeepSeek, hidden for others) -->
          <div v-if="provider.provider === 'deepseek' || forms[provider.provider].base_url">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Base URL</label>
            <UInput
              v-model="forms[provider.provider].base_url"
              placeholder="https://api.deepseek.com"
            />
          </div>

          <!-- Enable Toggle -->
          <div class="flex items-center gap-3">
            <USwitch v-model="forms[provider.provider].is_enabled" />
            <span class="text-sm text-gray-700 dark:text-gray-300">Enabled</span>
          </div>

          <!-- Last Test Result -->
          <div v-if="provider.last_tested_at" class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3 text-sm">
            <div class="flex items-center gap-2 mb-1">
              <UIcon
                :name="provider.test_status === 'success' ? 'i-heroicons-check-circle' : 'i-heroicons-x-circle'"
                :class="provider.test_status === 'success' ? 'text-green-500' : 'text-red-500'"
                class="w-4 h-4"
              />
              <span class="font-medium" :class="provider.test_status === 'success' ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'">
                {{ provider.test_status === 'success' ? 'Connection successful' : 'Connection failed' }}
              </span>
            </div>
            <p class="text-gray-500 dark:text-gray-400 text-xs">
              Tested {{ formatDate(provider.last_tested_at) }}
            </p>
            <p v-if="provider.test_error" class="text-red-600 dark:text-red-400 text-xs mt-1">
              {{ provider.test_error }}
            </p>
            <p v-if="testResults[provider.provider]?.response_time_ms" class="text-gray-500 dark:text-gray-400 text-xs mt-1">
              Response time: {{ testResults[provider.provider].response_time_ms }}ms
            </p>
          </div>

          <!-- Actions -->
          <div class="flex flex-wrap gap-3 pt-2">
            <UButton
              @click="saveProvider(provider.provider)"
              :loading="saving[provider.provider]"
              color="primary"
            >
              Save
            </UButton>
            <UButton
              @click="testProvider(provider.provider)"
              :loading="testing[provider.provider]"
              variant="outline"
              :disabled="!provider.has_api_key && !forms[provider.provider].api_key"
            >
              Test Connection
            </UButton>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const { canManageSystem } = usePermissions()
if (!canManageSystem.value) navigateTo('/dashboard')

const api = useApi()
const toast = useToast()

const loading = ref(true)
const providers = ref<any[]>([])
const forms = ref<Record<string, any>>({})
const saving = ref<Record<string, boolean>>({})
const testing = ref<Record<string, boolean>>({})
const testResults = ref<Record<string, any>>({})

const modelOptions: Record<string, { label: string; value: string }[]> = {
  openai: [
    { label: 'GPT-4o', value: 'gpt-4o' },
    { label: 'GPT-4o Mini', value: 'gpt-4o-mini' },
    { label: 'GPT-4 Turbo', value: 'gpt-4-turbo' },
    { label: 'o1', value: 'o1' },
    { label: 'o3 Mini', value: 'o3-mini' },
  ],
  anthropic: [
    { label: 'Claude Sonnet 4', value: 'claude-sonnet-4-20250514' },
    { label: 'Claude Opus 4', value: 'claude-opus-4-20250514' },
    { label: 'Claude Haiku 4', value: 'claude-haiku-4-20250514' },
  ],
  deepseek: [
    { label: 'DeepSeek Chat', value: 'deepseek-chat' },
    { label: 'DeepSeek Reasoner', value: 'deepseek-reasoner' },
  ],
}

function providerIcon(provider: string) {
  const icons: Record<string, string> = {
    openai: 'i-heroicons-sparkles',
    anthropic: 'i-heroicons-chat-bubble-left-right',
    deepseek: 'i-heroicons-magnifying-glass-circle',
  }
  return icons[provider] || 'i-heroicons-cpu-chip'
}

function providerIconBg(provider: string) {
  const bgs: Record<string, string> = {
    openai: 'bg-green-50 dark:bg-green-900/30',
    anthropic: 'bg-orange-50 dark:bg-orange-900/30',
    deepseek: 'bg-blue-50 dark:bg-blue-900/30',
  }
  return bgs[provider] || 'bg-gray-50 dark:bg-gray-900/30'
}

function providerIconColor(provider: string) {
  const colors: Record<string, string> = {
    openai: 'text-green-600 dark:text-green-400',
    anthropic: 'text-orange-600 dark:text-orange-400',
    deepseek: 'text-blue-600 dark:text-blue-400',
  }
  return colors[provider] || 'text-gray-600 dark:text-gray-400'
}

function statusColor(provider: any) {
  if (provider.test_status === 'success' && provider.is_enabled) return 'success' as const
  if (provider.test_status === 'failed') return 'error' as const
  if (provider.has_api_key) return 'warning' as const
  return 'neutral' as const
}

function statusLabel(provider: any) {
  if (provider.test_status === 'success' && provider.is_enabled) return 'Connected'
  if (provider.test_status === 'failed') return 'Failed'
  if (provider.has_api_key && !provider.is_enabled) return 'Disabled'
  if (provider.has_api_key) return 'Not tested'
  return 'Not configured'
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString()
}

async function loadProviders() {
  loading.value = true
  try {
    const data = await api.getAIProviders() as any[]
    providers.value = data
    for (const p of data) {
      forms.value[p.provider] = {
        api_key: '',
        default_model: p.default_model,
        base_url: p.base_url || '',
        is_enabled: p.is_enabled,
      }
    }
  } catch (e: any) {
    toast.add({ title: 'Error', description: e?.data?.detail || 'Failed to load providers', color: 'error' })
  } finally {
    loading.value = false
  }
}

async function saveProvider(provider: string) {
  saving.value[provider] = true
  try {
    const form = forms.value[provider]
    const payload: any = {
      default_model: form.default_model,
      is_enabled: form.is_enabled,
    }
    if (form.api_key) payload.api_key = form.api_key
    if (form.base_url !== undefined) payload.base_url = form.base_url || null

    await api.updateAIProvider(provider, payload)
    toast.add({ title: 'Saved', description: `${provider} configuration updated`, color: 'success' })
    forms.value[provider].api_key = ''
    await loadProviders()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e?.data?.detail || 'Failed to save', color: 'error' })
  } finally {
    saving.value[provider] = false
  }
}

async function testProvider(provider: string) {
  testing.value[provider] = true
  try {
    // Save first if there's a new API key
    if (forms.value[provider].api_key) {
      await saveProvider(provider)
    }
    const result = await api.testAIProvider(provider) as any
    testResults.value[provider] = result
    if (result.status === 'success') {
      toast.add({ title: 'Success', description: result.message, color: 'success' })
    } else {
      toast.add({ title: 'Failed', description: result.message, color: 'error' })
    }
    await loadProviders()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e?.data?.detail || 'Test failed', color: 'error' })
  } finally {
    testing.value[provider] = false
  }
}

onMounted(loadProviders)
</script>
