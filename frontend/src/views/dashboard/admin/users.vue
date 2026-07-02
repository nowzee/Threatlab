<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import '@/assets/css/admin-paper.css'

type AdminUser = { id: number; username: string; role: string; honeypot_count: number }

const auth = useAuthStore()
const users = ref<AdminUser[]>([])
const q = ref('')
const modal = ref(false)
const busy = ref(false)
const err = ref('')
const toast = ref('')
const form = reactive({ username: '', password: '', confirm: '' })
const showPwd = ref(false)
const showConfirm = ref(false)
const confirmUser = ref<AdminUser | null>(null)
const deleting = ref(false)

const filtered = computed(() => {
  const s = q.value.trim().toLowerCase()
  if (!s) return users.value
  return users.value.filter(u => u.username.toLowerCase().includes(s) || u.role.toLowerCase().includes(s))
})

async function load() {
  try {
    const res = await fetch('/api/admin/users', { credentials: 'include', headers: { Accept: 'application/json' } })
    const data = await res.json()
    if (res.ok && data.success) users.value = data.users
  } catch (e) { /* noop */ }
}
onMounted(load)

function openCreate() {
  form.username = ''
  form.password = ''
  form.confirm = ''
  showPwd.value = false
  showConfirm.value = false
  err.value = ''
  modal.value = true
}

async function create() {
  err.value = ''
  if (form.password !== form.confirm) {
    err.value = 'Les mots de passe ne correspondent pas'
    return
  }
  busy.value = true
  try {
    const res = await fetch('/api/admin/users', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ username: form.username, password: form.password }),
    })
    const data = await res.json()
    if (res.ok && data.success) {
      modal.value = false
      flash('Compte créé.')
      await load()
    } else {
      err.value = data.error || 'Erreur lors de la création'
    }
  } catch (e) {
    err.value = 'Erreur de connexion'
  } finally {
    busy.value = false
  }
}

function askDelete(u: AdminUser) { confirmUser.value = u }

async function doDelete() {
  if (!confirmUser.value) return
  deleting.value = true
  const id = confirmUser.value.id
  try {
    const res = await fetch(`/api/admin/users/${id}`, {
      method: 'DELETE',
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
    const data = await res.json()
    flash(res.ok && data.success ? 'Compte supprimé.' : (data.error || 'Suppression impossible'))
    confirmUser.value = null
    if (res.ok && data.success) await load()
  } catch (e) {
    flash('Erreur de connexion')
    confirmUser.value = null
  } finally {
    deleting.value = false
  }
}

function canDelete(u: AdminUser): boolean {
  return u.role !== 'admin' && u.username !== auth.user?.username
}

let toastTimer: ReturnType<typeof setTimeout>
function flash(m: string) {
  toast.value = m
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 2600)
}
</script>

<template>
  <div class="admin-paper content-wrapper">
    <div class="head">
      <div>
        <h1>Utilisateurs</h1>
        <p class="muted">Gérez les comptes ({{ users.length }}). Les nouveaux comptes sont créés en tant que membres.</p>
      </div>
      <div class="actions">
        <input v-model="q" class="input search" placeholder="Rechercher…" />
        <button class="btn btn-primary" @click="openCreate">+ Nouveau compte</button>
      </div>
    </div>

    <div class="card no-pad">
      <table class="t">
        <thead>
          <tr>
            <th>Utilisateur</th>
            <th style="width:140px">Rôle</th>
            <th style="width:120px">Honeypots</th>
            <th style="width:120px"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in filtered" :key="u.id">
            <td>
              <strong>{{ u.username }}</strong>
              <span v-if="u.username === auth.user?.username" class="mono small"> (vous)</span>
            </td>
            <td>
              <span class="pill" :class="u.role === 'admin' ? 'pill-bad' : 'pill-ok'"><span class="d"></span>{{ u.role }}</span>
            </td>
            <td class="mono">{{ u.honeypot_count }}</td>
            <td>
              <button v-if="canDelete(u)" class="btn btn-ghost btn-sm danger" @click="askDelete(u)">Supprimer</button>
            </td>
          </tr>
          <tr v-if="!filtered.length"><td colspan="4" class="empty">Aucun utilisateur</td></tr>
        </tbody>
      </table>
    </div>

    <!-- Create modal -->
    <div v-if="modal" class="modal-mask" @click.self="modal = false">
      <div class="modal">
        <h2>Nouveau compte</h2>
        <p class="sub">Créez un compte membre. Mot de passe : au moins 12 caractères, avec minuscule, majuscule, chiffre et caractère spécial.</p>
        <form @submit.prevent="create">
          <div class="field"><label class="label">Nom d'utilisateur</label><input v-model="form.username" required class="input" /></div>
          <div class="field">
            <label class="label">Mot de passe</label>
            <div class="pwd-wrap">
              <input v-model="form.password" :type="showPwd ? 'text' : 'password'" minlength="12" required class="input" />
              <button type="button" class="pwd-eye" @click="showPwd = !showPwd" :aria-label="showPwd ? 'Masquer le mot de passe' : 'Afficher le mot de passe'">
                <svg v-if="showPwd" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
              </button>
            </div>
          </div>
          <div class="field">
            <label class="label">Confirmer le mot de passe</label>
            <div class="pwd-wrap">
              <input v-model="form.confirm" :type="showConfirm ? 'text' : 'password'" minlength="12" required class="input" />
              <button type="button" class="pwd-eye" @click="showConfirm = !showConfirm" :aria-label="showConfirm ? 'Masquer le mot de passe' : 'Afficher le mot de passe'">
                <svg v-if="showConfirm" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
              </button>
            </div>
          </div>
          <div v-if="err" class="error">{{ err }}</div>
          <div class="modal-foot">
            <button type="button" class="btn btn-ghost" @click="modal = false">Annuler</button>
            <button type="submit" class="btn btn-primary" :disabled="busy">{{ busy ? 'Création…' : 'Créer le compte' }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete confirm modal -->
    <div v-if="confirmUser" class="modal-mask" @click.self="confirmUser = null">
      <div class="modal">
        <h2>Supprimer le compte</h2>
        <p class="sub">Confirmez la suppression de <strong>{{ confirmUser.username }}</strong>. Ses honeypots seront conservés mais dissociés du compte.</p>
        <div class="modal-foot">
          <button type="button" class="btn btn-ghost" @click="confirmUser = null">Annuler</button>
          <button type="button" class="btn btn-danger" :disabled="deleting" @click="doDelete">{{ deleting ? 'Suppression…' : 'Supprimer' }}</button>
        </div>
      </div>
    </div>

    <div v-if="toast" class="toast">{{ toast }}</div>
  </div>
</template>
