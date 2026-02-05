<script setup lang="ts">
/**
 * PatternRuleBuilder Component
 * UI for building and testing pattern matching rules for event categorization
 */

interface PatternRule {
  type: 'contains' | 'starts_with' | 'ends_with' | 'regex'
  value: string
  case_insensitive: boolean
}

const props = defineProps<{
  modelValue: { patterns: PatternRule[] }
}>()

const emit = defineEmits<{
  'update:modelValue': [value: { patterns: PatternRule[] }]
}>()

// Local state for patterns
const patterns = ref<PatternRule[]>([...(props.modelValue?.patterns || [])])

// Test input
const testInput = ref('')
const testResult = ref<{ matches: boolean, matchedPattern: number | null } | null>(null)

// Pattern type options
const patternTypes = [
  { value: 'contains', label: 'Contains', description: 'Text contains the value' },
  { value: 'starts_with', label: 'Starts with', description: 'Text starts with the value' },
  { value: 'ends_with', label: 'Ends with', description: 'Text ends with the value' },
  { value: 'regex', label: 'Regex', description: 'Matches regular expression' },
]

// Add new pattern
const addPattern = () => {
  patterns.value.push({
    type: 'contains',
    value: '',
    case_insensitive: true
  })
  emitUpdate()
}

// Remove pattern
const removePattern = (index: number) => {
  patterns.value.splice(index, 1)
  emitUpdate()
}

// Update pattern
const updatePattern = (index: number, field: keyof PatternRule, value: any) => {
  patterns.value[index][field] = value as never
  emitUpdate()
}

// Emit changes
const emitUpdate = () => {
  emit('update:modelValue', { patterns: patterns.value })
}

// Test patterns against input
const testPatterns = () => {
  if (!testInput.value) {
    testResult.value = { matches: false, matchedPattern: null }
    return
  }

  for (let i = 0; i < patterns.value.length; i++) {
    const pattern = patterns.value[i]
    if (matchesPattern(testInput.value, pattern)) {
      testResult.value = { matches: true, matchedPattern: i }
      return
    }
  }

  testResult.value = { matches: false, matchedPattern: null }
}

// Pattern matching logic (mirrors backend)
const matchesPattern = (text: string, pattern: PatternRule): boolean => {
  let testText = text
  let testValue = pattern.value

  if (pattern.case_insensitive) {
    testText = text.toLowerCase()
    testValue = pattern.value.toLowerCase()
  }

  try {
    switch (pattern.type) {
      case 'contains':
        return testText.includes(testValue)
      case 'starts_with':
        return testText.startsWith(testValue)
      case 'ends_with':
        return testText.endsWith(testValue)
      case 'regex':
        const flags = pattern.case_insensitive ? 'i' : ''
        return new RegExp(pattern.value, flags).test(text)
      default:
        return false
    }
  } catch (error) {
    return false
  }
}

// Watch for external changes
watch(() => props.modelValue, (newVal) => {
  patterns.value = [...(newVal?.patterns || [])]
}, { deep: true })
</script>

<template>
  <div class="space-y-4">
    <!-- Pattern Rules List -->
    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300">Pattern Rules</h3>
        <UButton
          icon="i-heroicons-plus"
          size="xs"
          color="primary"
          variant="soft"
          @click="addPattern"
        >
          Add Pattern
        </UButton>
      </div>

      <!-- Empty state -->
      <div
        v-if="patterns.length === 0"
        class="text-center py-8 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg"
      >
        <UIcon name="i-heroicons-funnel" class="w-8 h-8 mx-auto text-gray-400 mb-2" />
        <p class="text-sm text-gray-500">No pattern rules defined</p>
        <p class="text-xs text-gray-400 mt-1">Events will not match this category</p>
      </div>

      <!-- Pattern rules -->
      <div
        v-for="(pattern, index) in patterns"
        :key="index"
        class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg space-y-3"
      >
        <div class="flex items-start justify-between gap-2">
          <span class="text-xs font-medium text-gray-500">Pattern {{ index + 1 }}</span>
          <UButton
            icon="i-heroicons-trash"
            size="xs"
            color="red"
            variant="ghost"
            @click="removePattern(index)"
          />
        </div>

        <!-- Pattern type selector -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Match Type
            </label>
            <USelectMenu
              :model-value="pattern.type"
              :items="patternTypes"
              value-key="value"
              @update:model-value="updatePattern(index, 'type', $event)"
            >
              <template #label>
                {{ patternTypes.find(t => t.value === pattern.type)?.label }}
              </template>
              <template #item="{ item }">
                <div class="flex flex-col">
                  <span class="font-medium">{{ item.label }}</span>
                  <span class="text-xs text-gray-500">{{ item.description }}</span>
                </div>
              </template>
            </USelectMenu>
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Pattern Value
            </label>
            <UInput
              :model-value="pattern.value"
              placeholder="Enter pattern..."
              @update:model-value="updatePattern(index, 'value', $event)"
            />
          </div>
        </div>

        <!-- Case sensitivity toggle -->
        <UCheckbox
          :model-value="pattern.case_insensitive"
          label="Case insensitive"
          @update:model-value="updatePattern(index, 'case_insensitive', $event)"
        />
      </div>
    </div>

    <!-- Pattern Tester -->
    <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
      <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Test Patterns</h3>

      <div class="space-y-3">
        <div class="flex gap-2">
          <UInput
            v-model="testInput"
            placeholder="Enter event title to test..."
            class="flex-1"
            @keyup.enter="testPatterns"
          />
          <UButton
            icon="i-heroicons-play"
            @click="testPatterns"
            :disabled="!testInput || patterns.length === 0"
          >
            Test
          </UButton>
        </div>

        <!-- Test result -->
        <div
          v-if="testResult"
          class="p-3 rounded-lg"
          :class="testResult.matches ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800' : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'"
        >
          <div class="flex items-center gap-2">
            <UIcon
              :name="testResult.matches ? 'i-heroicons-check-circle' : 'i-heroicons-x-circle'"
              :class="testResult.matches ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'"
              class="w-5 h-5"
            />
            <div class="flex-1">
              <p
                class="text-sm font-medium"
                :class="testResult.matches ? 'text-green-800 dark:text-green-300' : 'text-red-800 dark:text-red-300'"
              >
                {{ testResult.matches ? 'Match Found!' : 'No Match' }}
              </p>
              <p
                v-if="testResult.matches && testResult.matchedPattern !== null"
                class="text-xs"
                :class="testResult.matches ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'"
              >
                Matched by Pattern {{ testResult.matchedPattern + 1 }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Help text -->
    <div class="text-xs text-gray-500 space-y-1">
      <p><strong>Contains:</strong> Matches if the event title contains the text</p>
      <p><strong>Starts with:</strong> Matches if the event title starts with the text</p>
      <p><strong>Ends with:</strong> Matches if the event title ends with the text</p>
      <p><strong>Regex:</strong> Matches using a regular expression pattern</p>
    </div>
  </div>
</template>
