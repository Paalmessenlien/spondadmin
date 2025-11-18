<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Skip to main content link for accessibility -->
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded"
    >
      Skip to main content
    </a>

    <!-- Navigation Header -->
    <header class="bg-white dark:bg-gray-800 shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <!-- Logo and Mobile Menu Button -->
          <div class="flex items-center space-x-4">
            <!-- Mobile menu button -->
            <UButton
              color="gray"
              variant="ghost"
              icon="i-heroicons-bars-3"
              class="md:hidden"
              aria-label="Open navigation menu"
              @click="mobileMenuOpen = true"
            />

            <h1 class="text-xl font-bold text-gray-900 dark:text-white">
              Spond Admin
            </h1>
          </div>

          <!-- Desktop Navigation -->
          <nav class="hidden md:flex space-x-2" aria-label="Main navigation">
            <UButton
              to="/dashboard"
              exact
              color="gray"
              variant="ghost"
              icon="i-heroicons-home"
              exact-active-class="!bg-blue-100 dark:!bg-blue-900 !text-blue-600 dark:!text-blue-400"
            >
              Dashboard
            </UButton>
            <UButton
              to="/dashboard/analytics"
              color="gray"
              variant="ghost"
              icon="i-heroicons-chart-bar"
              exact-active-class="!bg-blue-100 dark:!bg-blue-900 !text-blue-600 dark:!text-blue-400"
            >
              Analytics
            </UButton>
            <UButton
              to="/dashboard/events"
              color="gray"
              variant="ghost"
              icon="i-heroicons-calendar"
              exact-active-class="!bg-blue-100 dark:!bg-blue-900 !text-blue-600 dark:!text-blue-400"
            >
              Events
            </UButton>
            <UButton
              to="/dashboard/groups"
              color="gray"
              variant="ghost"
              icon="i-heroicons-user-group"
              exact-active-class="!bg-blue-100 dark:!bg-blue-900 !text-blue-600 dark:!text-blue-400"
            >
              Groups
            </UButton>
            <UButton
              to="/dashboard/members"
              color="gray"
              variant="ghost"
              icon="i-heroicons-users"
              exact-active-class="!bg-blue-100 dark:!bg-blue-900 !text-blue-600 dark:!text-blue-400"
            >
              Members
            </UButton>
          </nav>

          <!-- Group Selector and User Menu - Desktop -->
          <div class="hidden md:flex items-center space-x-4">
            <div class="w-48">
              <GroupSelector />
            </div>
            <div class="text-sm text-gray-700 dark:text-gray-300">
              {{ authStore.user?.full_name || authStore.user?.username }}
            </div>
            <UButton
              color="red"
              variant="soft"
              icon="i-heroicons-arrow-right-on-rectangle"
              aria-label="Logout"
              @click="handleLogout"
            >
              Logout
            </UButton>
          </div>

          <!-- User Menu - Mobile -->
          <div class="flex md:hidden items-center">
            <UButton
              color="gray"
              variant="ghost"
              icon="i-heroicons-user-circle"
              aria-label="Open user menu"
              @click="userMenuOpen = true"
            />
          </div>
        </div>
      </div>
    </header>

    <!-- Mobile Navigation Drawer -->
    <ClientOnly>
      <USlideover v-model="mobileMenuOpen" side="left" class="md:hidden">
        <div class="p-4 space-y-4">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Navigation
            </h2>
            <UButton
              color="gray"
              variant="ghost"
              icon="i-heroicons-x-mark"
              aria-label="Close navigation menu"
              @click="mobileMenuOpen = false"
            />
          </div>

          <nav class="space-y-2" aria-label="Mobile navigation">
            <UButton
              to="/dashboard"
              exact
              block
              color="gray"
              variant="ghost"
              icon="i-heroicons-home"
              exact-active-class="!bg-blue-100 dark:!bg-blue-900 !text-blue-600 dark:!text-blue-400"
              @click="mobileMenuOpen = false"
            >
              Dashboard
            </UButton>
            <UButton
              to="/dashboard/analytics"
              block
              color="gray"
              variant="ghost"
              icon="i-heroicons-chart-bar"
              exact-active-class="!bg-blue-100 dark:!bg-blue-900 !text-blue-600 dark:!text-blue-400"
              @click="mobileMenuOpen = false"
            >
              Analytics
            </UButton>
            <UButton
              to="/dashboard/events"
              block
              color="gray"
              variant="ghost"
              icon="i-heroicons-calendar"
              exact-active-class="!bg-blue-100 dark:!bg-blue-900 !text-blue-600 dark:!text-blue-400"
              @click="mobileMenuOpen = false"
            >
              Events
            </UButton>
            <UButton
              to="/dashboard/groups"
              block
              color="gray"
              variant="ghost"
              icon="i-heroicons-user-group"
              exact-active-class="!bg-blue-100 dark:!bg-blue-900 !text-blue-600 dark:!text-blue-400"
              @click="mobileMenuOpen = false"
            >
              Groups
            </UButton>
            <UButton
              to="/dashboard/members"
              block
              color="gray"
              variant="ghost"
              icon="i-heroicons-users"
              exact-active-class="!bg-blue-100 dark:!bg-blue-900 !text-blue-600 dark:!text-blue-400"
              @click="mobileMenuOpen = false"
            >
              Members
            </UButton>
          </nav>
        </div>
      </USlideover>
    </ClientOnly>

    <!-- Mobile User Menu -->
    <ClientOnly>
      <USlideover v-model="userMenuOpen" side="right" class="md:hidden">
        <div class="p-4 space-y-4">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Account
            </h2>
            <UButton
              color="gray"
              variant="ghost"
              icon="i-heroicons-x-mark"
              aria-label="Close user menu"
              @click="userMenuOpen = false"
            />
          </div>

          <div class="space-y-4">
            <div class="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
              <div class="flex items-center space-x-3">
                <div class="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold text-lg">
                  {{ getInitials(authStore.user?.full_name || authStore.user?.username) }}
                </div>
                <div>
                  <div class="font-medium text-gray-900 dark:text-white">
                    {{ authStore.user?.full_name || authStore.user?.username }}
                  </div>
                  <div class="text-sm text-gray-500 dark:text-gray-400">
                    {{ authStore.user?.email || '' }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Group Selector -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Select Group
              </label>
              <GroupSelector />
            </div>

            <UButton
              block
              color="red"
              variant="soft"
              icon="i-heroicons-arrow-right-on-rectangle"
              @click="handleLogout"
            >
              Logout
            </UButton>
          </div>
        </div>
      </USlideover>
    </ClientOnly>

    <!-- Main Content -->
    <main id="main-content" class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
const authStore = useAuthStore()

// Mobile menu state - ensure they start closed
const mobileMenuOpen = ref(false)
const userMenuOpen = ref(false)

// Initialize auth on mount and ensure menus are closed
onMounted(async () => {
  // Explicitly close menus
  mobileMenuOpen.value = false
  userMenuOpen.value = false

  if (!authStore.token) {
    await authStore.initAuth()
  }
})

const handleLogout = () => {
  authStore.logout()
  mobileMenuOpen.value = false
  userMenuOpen.value = false
}

// Helper function to get user initials
const getInitials = (name: string | undefined) => {
  if (!name) return '?'
  const names = name.split(' ')
  if (names.length >= 2) {
    return (names[0][0] + names[names.length - 1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}
</script>
