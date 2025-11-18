<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
    <UCard class="w-full max-w-md">
      <template #header>
        <div class="text-center">
          <h2 class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
            Spond Admin
          </h2>
          <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Sign in to your account
          </p>
        </div>
      </template>

      <UForm
        :state="state"
        :schema="schema"
        @submit="handleLogin"
        class="space-y-4"
      >
        <UFormField label="Username" name="username">
          <UInput
            v-model="state.username"
            placeholder="Enter your username"
            icon="i-heroicons-user"
            size="lg"
            :disabled="loading"
            autocomplete="username"
            aria-label="Username"
          />
        </UFormField>

        <UFormField label="Password" name="password">
          <UInput
            v-model="state.password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="Enter your password"
            icon="i-heroicons-lock-closed"
            size="lg"
            :disabled="loading"
            autocomplete="current-password"
            aria-label="Password"
          >
            <template #trailing>
              <UButton
                color="gray"
                variant="ghost"
                :icon="showPassword ? 'i-heroicons-eye-slash' : 'i-heroicons-eye'"
                size="xs"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
                @click="showPassword = !showPassword"
              />
            </template>
          </UInput>
        </UFormField>

        <!-- Remember Me -->
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <input
              id="remember-me"
              v-model="state.rememberMe"
              type="checkbox"
              class="h-4 w-4 rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 dark:bg-gray-800"
            />
            <label for="remember-me" class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
              Remember me
            </label>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="rounded-lg bg-red-50 dark:bg-red-900/20 p-3 border border-red-200 dark:border-red-800">
          <div class="flex items-start">
            <UIcon name="i-heroicons-exclamation-circle" class="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
            <div class="ml-2 text-sm text-red-700 dark:text-red-300">
              {{ error }}
            </div>
          </div>
        </div>

        <UButton
          type="submit"
          block
          size="lg"
          :loading="loading"
          :disabled="loading || !state.username || !state.password"
        >
          {{ loading ? 'Signing in...' : 'Sign in' }}
        </UButton>
      </UForm>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { z } from 'zod'

// Redirect if already authenticated
const authStore = useAuthStore()
const router = useRouter()

if (authStore.isAuthenticated) {
  navigateTo('/dashboard')
}

const schema = z.object({
  username: z.string()
    .min(1, 'Username is required')
    .min(3, 'Username must be at least 3 characters'),
  password: z.string()
    .min(1, 'Password is required')
    .min(6, 'Password must be at least 6 characters'),
  rememberMe: z.boolean().optional(),
})

const state = reactive({
  username: '',
  password: '',
  rememberMe: false,
})

const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

// Load saved credentials if Remember Me was checked
onMounted(() => {
  if (import.meta.client) {
    const savedUsername = localStorage.getItem('remembered_username')
    const rememberMe = localStorage.getItem('remember_me') === 'true'

    if (rememberMe && savedUsername) {
      state.username = savedUsername
      state.rememberMe = true
    }
  }
})

const handleLogin = async () => {
  loading.value = true
  error.value = ''

  try {
    const success = await authStore.login(state.username, state.password)

    if (success) {
      // Handle Remember Me
      if (import.meta.client) {
        if (state.rememberMe) {
          localStorage.setItem('remembered_username', state.username)
          localStorage.setItem('remember_me', 'true')
        } else {
          localStorage.removeItem('remembered_username')
          localStorage.removeItem('remember_me')
        }
      }

      navigateTo('/dashboard')
    } else {
      error.value = 'Invalid username or password. Please check your credentials and try again.'
    }
  } catch (err: any) {
    console.error('Login error:', err)

    // Provide more specific error messages
    const errorDetail = err?.data?.detail

    if (errorDetail?.includes('Incorrect username')) {
      error.value = 'Username not found. Please check your username and try again.'
    } else if (errorDetail?.includes('Incorrect password')) {
      error.value = 'Incorrect password. Please try again.'
    } else if (errorDetail?.includes('inactive')) {
      error.value = 'Your account has been deactivated. Please contact an administrator.'
    } else {
      error.value = errorDetail || 'Login failed. Please check your credentials and try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>
