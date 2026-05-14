// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },

  modules: [
    '@nuxt/ui',
    '@pinia/nuxt',
  ],

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    // Public keys (exposed to client)
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8001/api/v1'
    }
  },

  app: {
    head: {
      title: 'Archery Club Admin',
      // `en-GB` forces native time/date inputs into 24-hour format (and
      // DD/MM/YYYY for dates) regardless of OS locale. Without this the
      // browser falls back to e.g. en-US which renders time as AM/PM.
      htmlAttrs: { lang: 'en-GB' },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Archery club administration with Spond integration' }
      ],
    }
  },
})
