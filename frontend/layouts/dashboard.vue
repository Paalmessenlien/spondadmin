<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Skip to main content link for accessibility -->
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded"
    >
      Skip to main content
    </a>

    <!-- Mobile Header -->
    <header class="md:hidden bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
      <div class="flex justify-between items-center h-14 px-4">
        <div class="flex items-center space-x-3">
          <UButton
            color="gray"
            variant="ghost"
            icon="i-heroicons-bars-3"
            aria-label="Open navigation menu"
            @click="mobileMenuOpen = true"
          />
          <span class="text-lg font-bold text-gray-900 dark:text-white">{{ clubName }}</span>
        </div>
        <UButton
          color="gray"
          variant="ghost"
          icon="i-heroicons-user-circle"
          aria-label="Open user menu"
          @click="userMenuOpen = true"
        />
      </div>
    </header>

    <!-- Desktop Sidebar -->
    <aside class="hidden md:flex md:flex-col md:fixed md:inset-y-0 md:left-0 md:w-[260px] bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 z-30">
      <!-- Club Header -->
      <div class="flex items-center space-x-3 px-5 h-16 border-b border-gray-200 dark:border-gray-700">
        <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
          <UIcon name="i-heroicons-viewfinder-circle" class="w-5 h-5 text-white" />
        </div>
        <span class="text-lg font-bold text-gray-900 dark:text-white">{{ clubName }}</span>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 overflow-y-auto py-4 px-3 space-y-6" aria-label="Main navigation">
        <div v-for="group in navGroups" :key="group.label">
          <p class="px-3 mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
            {{ group.label }}
          </p>
          <div class="space-y-1">
            <NuxtLink
              v-for="item in group.items"
              :key="item.to"
              :to="item.comingSoon ? undefined : item.to"
              :class="[
                'flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive(item)
                  ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                  : item.comingSoon
                    ? 'text-gray-400 dark:text-gray-500 cursor-default'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/50'
              ]"
            >
              <UIcon :name="item.icon" class="w-5 h-5 mr-3 flex-shrink-0" />
              <span class="flex-1">{{ item.label }}</span>
              <span
                v-if="item.comingSoon"
                class="ml-2 px-1.5 py-0.5 text-[10px] font-medium rounded bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500"
              >
                Soon
              </span>
            </NuxtLink>
          </div>
        </div>
      </nav>

      <!-- Group Selector -->
      <div class="px-4 py-3 border-t border-gray-200 dark:border-gray-700">
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">Group</label>
        <GroupSelector />
      </div>

      <!-- User Profile -->
      <div class="px-4 py-3 border-t border-gray-200 dark:border-gray-700">
        <div class="flex items-center space-x-3">
          <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
            {{ getInitials(authStore.user?.full_name || authStore.user?.username) }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
              {{ authStore.user?.full_name || authStore.user?.username }}
            </p>
          </div>
          <UButton
            color="red"
            variant="ghost"
            icon="i-heroicons-arrow-right-on-rectangle"
            size="xs"
            aria-label="Logout"
            @click="handleLogout"
          />
        </div>
      </div>
    </aside>

    <!-- Mobile Navigation Drawer -->
    <ClientOnly>
      <USlideover v-model="mobileMenuOpen" side="left" class="md:hidden">
        <div class="flex flex-col h-full">
          <div class="flex justify-between items-center px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
                <UIcon name="i-heroicons-viewfinder-circle" class="w-5 h-5 text-white" />
              </div>
              <span class="text-lg font-bold text-gray-900 dark:text-white">{{ clubName }}</span>
            </div>
            <UButton
              color="gray"
              variant="ghost"
              icon="i-heroicons-x-mark"
              aria-label="Close navigation menu"
              @click="mobileMenuOpen = false"
            />
          </div>

          <nav class="flex-1 overflow-y-auto py-4 px-3 space-y-6" aria-label="Mobile navigation">
            <div v-for="group in navGroups" :key="group.label">
              <p class="px-3 mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
                {{ group.label }}
              </p>
              <div class="space-y-1">
                <NuxtLink
                  v-for="item in group.items"
                  :key="item.to"
                  :to="item.comingSoon ? undefined : item.to"
                  :class="[
                    'flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive(item)
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                      : item.comingSoon
                        ? 'text-gray-400 dark:text-gray-500 cursor-default'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/50'
                  ]"
                  @click="!item.comingSoon && (mobileMenuOpen = false)"
                >
                  <UIcon :name="item.icon" class="w-5 h-5 mr-3 flex-shrink-0" />
                  <span class="flex-1">{{ item.label }}</span>
                  <span
                    v-if="item.comingSoon"
                    class="ml-2 px-1.5 py-0.5 text-[10px] font-medium rounded bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500"
                  >
                    Soon
                  </span>
                </NuxtLink>
              </div>
            </div>
          </nav>

          <!-- Group Selector (Mobile) -->
          <div class="px-4 py-3 border-t border-gray-200 dark:border-gray-700">
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">Group</label>
            <GroupSelector />
          </div>
        </div>
      </USlideover>
    </ClientOnly>

    <!-- Mobile User Menu -->
    <ClientOnly>
      <USlideover v-model="userMenuOpen" side="right" class="md:hidden">
        <div class="p-4 space-y-4">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Account</h2>
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
                  <div class="text-sm text-gray-600 dark:text-gray-400">
                    {{ authStore.user?.email || '' }}
                  </div>
                </div>
              </div>
            </div>

            <UButton
              block
              color="red"
              variant="outline"
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
    <main id="main-content" class="md:ml-[260px]">
      <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const authStore = useAuthStore()

const mobileMenuOpen = ref(false)
const userMenuOpen = ref(false)

const clubName = ref('Archery Club')

// Fetch club name from backend
onMounted(async () => {
  mobileMenuOpen.value = false
  userMenuOpen.value = false

  try {
    const config = useRuntimeConfig()
    const data = await $fetch<{ club_name: string }>('/config/public', {
      baseURL: config.public.apiBase,
    })
    if (data?.club_name) {
      clubName.value = data.club_name
    }
  } catch {
    // Use default club name
  }
})

const { canManageSystem } = usePermissions()

interface NavItem {
  label: string
  to: string
  icon: string
  exact?: boolean
  comingSoon?: boolean
  minRole?: 'admin' | 'editor' | 'viewer'
}

interface NavGroup {
  label: string
  items: NavItem[]
}

const allNavGroups: NavGroup[] = [
  {
    label: 'Core',
    items: [
      { label: 'Dashboard', to: '/dashboard', icon: 'i-heroicons-home', exact: true },
    ],
  },
  {
    label: 'People',
    items: [
      { label: 'Members', to: '/dashboard/members', icon: 'i-heroicons-users' },
    ],
  },
  {
    label: 'Activities',
    items: [
      { label: 'Events & Training', to: '/dashboard/events', icon: 'i-heroicons-calendar' },
      { label: 'Training plan', to: '/dashboard/training', icon: 'i-heroicons-clipboard-document-list' },
      { label: 'Konkurranser', to: '/dashboard/competitions', icon: 'i-heroicons-trophy' },
    ],
  },
  {
    label: 'Performance',
    items: [
      { label: 'Scores & Records', to: '/dashboard/scores', icon: 'i-heroicons-viewfinder-circle' },
    ],
  },
  {
    label: 'Operations',
    items: [
      { label: 'Equipment', to: '/dashboard/equipment', icon: 'i-heroicons-cube', comingSoon: true },
      { label: 'Finances', to: '/dashboard/finances', icon: 'i-heroicons-credit-card', comingSoon: true },
      { label: 'Communication', to: '/dashboard/communication', icon: 'i-heroicons-bell', comingSoon: true },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { label: 'Reports', to: '/dashboard/reports', icon: 'i-heroicons-document-chart-bar' },
      { label: 'Analytics', to: '/dashboard/analytics', icon: 'i-heroicons-chart-bar' },
    ],
  },
  {
    label: 'System',
    items: [
      { label: 'Settings', to: '/dashboard/settings', icon: 'i-heroicons-cog-6-tooth', minRole: 'admin' },
    ],
  },
]

const navGroups = computed(() => {
  const roleLevel = { admin: 3, editor: 2, viewer: 1 }
  const userRole = authStore.user?.role ?? 'viewer'
  const userLevel = roleLevel[userRole] || 1

  return allNavGroups
    .map(group => ({
      ...group,
      items: group.items.filter(item => {
        const minLevel = roleLevel[item.minRole ?? 'viewer'] || 1
        return userLevel >= minLevel
      }),
    }))
    .filter(group => group.items.length > 0)
})

const isActive = (item: NavItem): boolean => {
  if (item.comingSoon) return false
  if (item.exact) return route.path === item.to
  return route.path.startsWith(item.to)
}

const clerk = useClerk()
const handleLogout = async () => {
  mobileMenuOpen.value = false
  userMenuOpen.value = false
  authStore.clearLocalState()
  try {
    if (clerk.value) await clerk.value.signOut()
  } catch (e) {
    console.error('Sign-out failed', e)
  }
  navigateTo('/login')
}

const getInitials = (name: string | undefined) => {
  if (!name) return '?'
  const names = name.split(' ')
  if (names.length >= 2) {
    return (names[0][0] + names[names.length - 1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}
</script>
