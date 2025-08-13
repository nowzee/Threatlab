import { defineStore } from 'pinia'

type Credentials = { username: string; password: string }
type SessionJson = {
  authenticated: boolean
  requires_a2f?: boolean
  error?: string
}

export const useAuthStore = defineStore('auth', {
    state: () => ({
        isAuthenticated: false as boolean,
        requires_a2f: false as boolean,
        error: null as string | null,
        hasCheckedSession: false,
    }),
  actions: {
    async login(credentials: Credentials) {
        this.error = null
        this.requires_a2f = false

        try {
          const res = await fetch('/auth/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: JSON.stringify(credentials),
            credentials: 'include',
          })

          if (!res.ok) {
            const errorData = await res.json()
            this.error = errorData.error || 'Erreur de connexion'
            return
          }

          const data = (await res.json()) as SessionJson

          if (data.error) {
            this.error = data.error
            return
          }

          this.isAuthenticated = data.authenticated
            if (data.requires_a2f) {
                this.requires_a2f = data.requires_a2f
            }
          this.hasCheckedSession = true;
          
        } catch (e: any) {
          this.error = e?.message || 'Erreur de connexion'
          this.hasCheckedSession = true;
        }
    },

    async fetchSession(force = false) {
      if (!force) return
      this.error = null
      try {
        const res = await fetch('/auth/session', {
          method: 'GET',
          headers: { 'Accept': 'application/json' },
          credentials: 'include',
        })

        if (!res.ok) {
          this.isAuthenticated = false
          this.requires_a2f = false
            this.hasCheckedSession = true
          return
        }

        const data = (await res.json()) as SessionJson
        // authenticated reste true même si A2F requis
          this.isAuthenticated = data.authenticated
          this.requires_a2f = !!data.requires_a2f
          this.hasCheckedSession = true

      } catch (e: any) {
          this.isAuthenticated = false
          this.requires_a2f = false
          this.error = e?.message || 'Erreur inconnue'
          this.hasCheckedSession = true

      }
    },

    async verifyA2F(code: string) {
      this.error = null

      try {
        const res = await fetch('/auth/a2f', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({ code }),
          credentials: 'include',
        })

        if (!res.ok) {
          const errorData = await res.json()
          throw new Error(errorData.error || 'Code de vérification invalide')
        }

        const data = await res.json()
        this.requires_a2f = !!data.requires_a2f
        
      } catch (e: any) {
        this.error = e?.message || 'Erreur de vérification'
        throw e
      }
    },

    async logout() {
      try {
        await fetch('/auth/logout', {
          method: 'GET',
          credentials: 'include',
        })
      } catch {
        // ignorer erreurs réseau
      } finally {
        this.isAuthenticated = false
        this.requires_a2f = false
      }
    },
  },
})