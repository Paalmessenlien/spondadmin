<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Settings' }
    ]" />

    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
        Manage club configuration, categories, and data sync
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Categories -->
      <UCard class="hover:border-blue-300 dark:hover:border-blue-700 transition-colors cursor-pointer" @click="navigateTo('/dashboard/settings/categories')">
        <div class="flex items-start space-x-4">
          <div class="w-12 h-12 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
            <UIcon name="i-heroicons-tag" class="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Event Categories</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Define categories and pattern rules for automatic event classification.
            </p>
          </div>
        </div>
      </UCard>

      <!-- Spond Sync -->
      <UCard class="hover:border-blue-300 dark:hover:border-blue-700 transition-colors cursor-pointer" @click="navigateTo('/dashboard/settings/sync')">
        <div class="flex items-start space-x-4">
          <div class="w-12 h-12 rounded-lg bg-green-50 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0">
            <UIcon name="i-heroicons-arrow-path" class="w-6 h-6 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Spond Sync</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Manage data synchronization with Spond. Run manual syncs and view scheduler status.
            </p>
          </div>
        </div>
      </UCard>

      <!-- Competition Scraper -->
      <UCard class="hover:border-blue-300 dark:hover:border-blue-700 transition-colors cursor-pointer" @click="navigateTo('/dashboard/settings/scraper')">
        <div class="flex items-start space-x-4">
          <div class="w-12 h-12 rounded-lg bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center flex-shrink-0">
            <UIcon name="i-heroicons-viewfinder-circle" class="w-6 h-6 text-amber-600 dark:text-amber-400" />
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Competition Scraper</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Configure scraping from bueskyting.no, manage archer matching, and view scrape history.
            </p>
          </div>
        </div>
      </UCard>

      <!-- Admin Users -->
      <UCard class="hover:border-blue-300 dark:hover:border-blue-700 transition-colors cursor-pointer" @click="navigateTo('/dashboard/settings/users')">
        <div class="flex items-start space-x-4">
          <div class="w-12 h-12 rounded-lg bg-purple-50 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0">
            <UIcon name="i-heroicons-shield-check" class="w-6 h-6 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Admin Users</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Manage administrator accounts, roles, and permissions.
            </p>
          </div>
        </div>
      </UCard>

      <!-- Roles & Access Groups -->
      <UCard class="hover:border-blue-300 dark:hover:border-blue-700 transition-colors cursor-pointer" @click="navigateTo('/dashboard/settings/access')">
        <div class="flex items-start space-x-4">
          <div class="w-12 h-12 rounded-lg bg-indigo-50 dark:bg-indigo-900/30 flex items-center justify-center flex-shrink-0">
            <UIcon name="i-heroicons-key" class="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Roles &amp; Access Groups</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Edit each role's default modules and create reusable access groups to assign to users.
            </p>
          </div>
        </div>
      </UCard>

      <!-- Database Backups -->
      <UCard class="hover:border-blue-300 dark:hover:border-blue-700 transition-colors cursor-pointer" @click="navigateTo('/dashboard/settings/backups')">
        <div class="flex items-start space-x-4">
          <div class="w-12 h-12 rounded-lg bg-teal-50 dark:bg-teal-900/30 flex items-center justify-center flex-shrink-0">
            <UIcon name="i-heroicons-circle-stack" class="w-6 h-6 text-teal-600 dark:text-teal-400" />
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Database Backups</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Create, restore, and manage database backups. Upload to CDN for offsite storage.
            </p>
          </div>
        </div>
      </UCard>

      <!-- AI Providers -->
      <UCard class="hover:border-rose-300 dark:hover:border-rose-700 transition-colors cursor-pointer" @click="navigateTo('/dashboard/settings/ai-providers')">
        <div class="flex items-start space-x-4">
          <div class="w-12 h-12 rounded-lg bg-rose-50 dark:bg-rose-900/30 flex items-center justify-center flex-shrink-0">
            <UIcon name="i-heroicons-cpu-chip" class="w-6 h-6 text-rose-600 dark:text-rose-400" />
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">AI Providers</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Configure API keys and settings for OpenAI, Anthropic, and DeepSeek integrations.
            </p>
          </div>
        </div>
      </UCard>

      <!-- Migrations -->
      <UCard class="hover:border-blue-300 dark:hover:border-blue-700 transition-colors cursor-pointer" @click="navigateTo('/dashboard/settings/migrations')">
        <div class="flex items-start space-x-4">
          <div class="w-12 h-12 rounded-lg bg-indigo-50 dark:bg-indigo-900/30 flex items-center justify-center flex-shrink-0">
            <UIcon name="i-heroicons-server-stack" class="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Migrations</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              View database migration status and apply pending schema changes.
            </p>
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
</script>
