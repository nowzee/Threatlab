<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { authErrorKey } from '@/i18n'
import LangSwitch from '@/components/LangSwitch.vue'

const { t } = useI18n()

const username = ref('')
const password = ref('')

const router = useRouter()
const auth = useAuthStore()

const errorText = computed(() => {
  const key = authErrorKey(auth.error)
  return key ? t(key) : auth.error
})

const onSubmit = async () => {
    await auth.login({username: username.value, password: password.value})

    if (auth.requires_a2f) {
      await router.push({name: 'a2f'});
      return;
    }

    if (auth.isAuthenticated) {
      await router.push({name: 'home'});
    }
}
</script>

<template>
  <div class="auth-shell">
    <!-- Colonne gauche : formulaire -->
    <main class="auth-main">
      <LangSwitch />
      <div class="login-wrap">
        <div class="brand">
          <svg width="56" height="56" viewBox="0 0 64 64" fill="none">
            <path d="M24 8 L24 22 L12 50 Q10 56 16 56 L48 56 Q54 56 52 50 L40 22 L40 8"
                  stroke="#F4F2ED" stroke-width="3"/>
            <path d="M22 8 L42 8" stroke="#F4F2ED" stroke-width="3"/>
            <polygon points="32,42 22,52 42,52" fill="var(--accent-color)"/>
          </svg>
          <span class="b-name">Threatlab</span>
        </div>

        <div class="kicker mono">{{ t('login.kicker') }}</div>
        <h1>{{ t('login.title') }}</h1>
        <p class="lead">{{ t('login.lead') }}</p>

        <form class="form" @submit.prevent="onSubmit">
          <div class="field">
            <label class="label">{{ t('login.username') }}</label>
            <input v-model="username" type="text" class="input" :placeholder="t('login.username')"
                   autocomplete="username" required />
          </div>

          <div class="field">
            <label class="label">{{ t('login.password') }}</label>
            <input v-model="password" type="password" class="input" placeholder="••••••••"
                   autocomplete="current-password" required />
          </div>

          <div v-if="auth.error" class="error">
            <span>{{ errorText }}</span>
          </div>

          <button type="submit" class="btn-block">{{ t('login.submit') }}</button>

          <p class="info mono">
            {{ t('login.info1') }}
            <br/>
            {{ t('login.info2') }}
          </p>
        </form>
      </div>
    </main>

    <!-- Colonne droite : panneau d'information -->
    <aside class="auth-side">
      <div class="side-body">
        <h2>{{ t('side.title') }}</h2>
        <p class="side-lead">
          {{ t('side.leadPre') }}<em>{{ t('side.leadEm') }}</em>{{ t('side.leadPost') }}
        </p>

        <div class="stats">
          <div class="stat">
            <div class="num">100%</div>
            <div class="lbl mono">{{ t('side.stat1') }}</div>
          </div>
          <div class="stat">
            <div class="num">15+</div>
            <div class="lbl mono">{{ t('side.stat2') }}</div>
          </div>
          <div class="stat">
            <div class="num">0</div>
            <div class="lbl mono">{{ t('side.stat3') }}</div>
          </div>
          <div class="stat">
            <div class="num">24/7</div>
            <div class="lbl mono">{{ t('side.stat4') }}</div>
          </div>
        </div>
      </div>

      <div class="side-foot mono">
        {{ t('side.foot') }}
      </div>
    </aside>
  </div>
</template>

<style scoped>
.auth-shell {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100vh;
  font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  color: var(--text-color);
}
.mono { font-family: 'JetBrains Mono', ui-monospace, 'Courier New', monospace; }

/* ---------- Colonne gauche : formulaire ---------- */
.auth-main {
  position: relative;
  background: var(--container-background);
  padding: 40px;
  display: flex; align-items: center; justify-content: center;
}
.login-wrap { width: 100%; max-width: 480px; }

.brand { display: flex; align-items: center; gap: 14px; margin-bottom: 44px; }
.b-name { font-size: 26px; font-weight: 700; letter-spacing: -.5px; color: var(--white); }

.kicker {
  font-size: 11px; letter-spacing: 1.5px;
  color: var(--text-color-muted); text-transform: uppercase; margin-bottom: 18px;
}
h1 { font-size: 38px; font-weight: 700; letter-spacing: -1px; margin: 0 0 12px; color: var(--white); }
.lead { color: var(--text-color-muted); margin: 0 0 36px; font-size: 15px; }

.form { display: flex; flex-direction: column; gap: 18px; }
.field { display: flex; flex-direction: column; }
.label {
  font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
  color: var(--text-color-muted); margin-bottom: 9px;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}
.input {
  width: 100%; box-sizing: border-box;
  padding: 15px 16px;
  background: var(--input-background);
  border: 1px solid var(--input-border);
  font-size: 16px; color: var(--white);
  transition: all 0.2s ease;
}
.input:focus {
  outline: none;
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 2px rgba(156, 77, 255, 0.18);
}
.btn-block {
  width: 100%; padding: 16px; margin-top: 6px;
  background: var(--button-background); color: var(--button-text);
  border: none; cursor: pointer;
  font-size: 15px; font-weight: 600;
  transition: all 0.2s ease;
}
.btn-block:hover { background: var(--button-hover-background-login); }

.error {
  background: rgba(255, 0, 46, 0.18);
  border-left: 3px solid var(--danger-color);
  padding: 10px 14px; font-size: 13px;
  display: flex; gap: 10px; align-items: center; color: var(--white);
}
.error .mono { color: #ff6b6b; font-weight: 700; }
.info { font-size: 11px; color: var(--text-color-muted); margin: 8px 0 0; line-height: 1.6; }
.info a { color: var(--accent-color); text-decoration: underline; }

/* ---------- Colonne droite : info ---------- */
.auth-side {
  background: var(--background-color-dark);
  color: var(--white);
  padding: 56px;
  display: flex; flex-direction: column; gap: 40px;
  position: relative; overflow: hidden;
  border-left: 1px solid var(--container-border-color);
}
.auth-side::before {
  content: ''; position: absolute; right: -220px; bottom: -220px;
  width: 520px; height: 520px;
  background: radial-gradient(circle, var(--accent-color) 0%, transparent 65%);
  opacity: .16; pointer-events: none;
}
.side-body { flex: 1; position: relative; max-width: 500px; display: flex; flex-direction: column; gap: 36px; justify-content: center; }
.side-body h2 { font-size: 36px; font-weight: 700; letter-spacing: -1px; line-height: 1.1; margin: 0; color: var(--white); }
.side-lead { font-size: 15px; color: var(--text-color-muted); margin: 0; line-height: 1.6; }
.side-lead em { font-style: normal; color: var(--accent-color); font-weight: 500; }

.stats {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 0;
  border: 1px solid var(--container-border-color);
}
.stat {
  padding: 22px 24px;
  border-right: 1px solid var(--container-border-color);
  border-bottom: 1px solid var(--container-border-color);
}
.stat:nth-child(2n) { border-right: 0; }
.stat:nth-last-child(-n+2) { border-bottom: 0; }
.num { font-size: 28px; font-weight: 700; letter-spacing: -1px; line-height: 1; margin-bottom: 8px; color: var(--white); }
.lbl { font-size: 10px; letter-spacing: 1.2px; color: var(--text-color-muted); }

.side-foot { font-size: 10px; color: var(--text-color-muted); letter-spacing: 1px; position: relative; }

/* ---------- Responsive ---------- */
@media (max-width: 900px) {
  .auth-shell { grid-template-columns: 1fr; }
  .auth-side { display: none; }
}
</style>
