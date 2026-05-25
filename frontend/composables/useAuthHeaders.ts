/**
 * Reactive Authorization header backed by Clerk's session token.
 *
 * Used by components that bypass useApi() and call $fetch / useFetch
 * directly (e.g. PDF/blob downloads, multipart uploads, reactive
 * dashboard fetches). The returned ``headers`` ref refreshes whenever
 * Clerk reports a new signed-in state so consumers using ``useFetch``
 * automatically refetch once the token is available.
 */
export function useAuthHeaders() {
  const { getToken, isLoaded, isSignedIn } = useAuth()
  const token = ref<string | null>(null)

  watchEffect(async () => {
    if (!isLoaded.value || !isSignedIn.value) {
      token.value = null
      return
    }
    try {
      token.value = await getToken.value()
    } catch {
      token.value = null
    }
  })

  const headers = computed<Record<string, string>>(() =>
    token.value ? { Authorization: `Bearer ${token.value}` } : {}
  )

  return { headers, token }
}
