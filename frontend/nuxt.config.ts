// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },

  modules: [
    '@nuxt/ui',
    '@pinia/nuxt',
    '@clerk/nuxt',
  ],

  css: ['~/assets/css/main.css'],

  // The dashboard is a client-authed SPA: the auth middleware bails out on the
  // server (`if (import.meta.server) return`), so SSR can only ever render a
  // logged-out shell that the client immediately corrects — which is exactly
  // what produces hydration mismatches on every role-gated element (sidebar
  // user menu, admin-only header buttons, etc.). Rendering these routes
  // client-side only removes that whole class of warning. No SEO cost: the
  // app sits entirely behind Clerk auth. Public routes (/login, /) keep SSR.
  routeRules: {
    '/dashboard': { ssr: false },
    '/dashboard/**': { ssr: false },
  },

  runtimeConfig: {
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
