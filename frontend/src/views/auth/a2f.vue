<script lang="ts" setup>
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { authErrorKey } from '@/i18n'
import LangSwitch from '@/components/LangSwitch.vue'

const { t } = useI18n()

const codeInputs = ref<string[]>(['', '', '', '', '', ''])
const inputRefs = ref<HTMLInputElement[]>([])
const error = ref<string | null>(null)

const router = useRouter()
const auth = useAuthStore()

const errorText = computed(() => {
  const key = authErrorKey(error.value)
  return key ? t(key) : error.value
})

const onInput = async (index: number, event: Event) => {
  const target = event.target as HTMLInputElement
  const value = target.value
  
  // Garder seulement le dernier caractère si plusieurs sont saisis
  if (value.length > 1) {
    codeInputs.value[index] = value.slice(-1)
    await nextTick()
  } else {
    codeInputs.value[index] = value
  }

  // Se déplacer au champ suivant si une valeur est saisie
  if (value && index < 5) {
    await nextTick()
    inputRefs.value[index + 1]?.focus()
  }

  checkAndSubmit()
}

const onKeydown = async (index: number, event: KeyboardEvent) => {
  if (event.key === 'Backspace' && !codeInputs.value[index] && index > 0) {
    codeInputs.value[index - 1] = ''
    await nextTick()
    inputRefs.value[index - 1]?.focus()
  }
}

const onPaste = async (index: number, event: ClipboardEvent) => {
  event.preventDefault()
  
  const pastedData = event.clipboardData?.getData('text') || ''
  const digits = pastedData.replace(/[^0-9]/g, '')

  // Remplir les champs à partir du champ actuel
  for (let j = 0; j < digits.length && (index + j) < 6; j++) {
    codeInputs.value[index + j] = digits[j] || ''
  }

  // Déplacer le focus au dernier champ rempli ou au suivant
  const lastFilledIndex = Math.min(index + digits.length - 1, 5)
  const nextIndex = Math.min(index + digits.length, 5)

  await nextTick()
  if (lastFilledIndex < 5) {
    inputRefs.value[nextIndex]?.focus()
  } else {
    inputRefs.value[lastFilledIndex]?.focus()
  }

  checkAndSubmit()
}

const checkAndSubmit = async () => {
  const code = codeInputs.value.join('')
  const allFilled = codeInputs.value.every(val => val && val.match(/^[0-9]$/))

  if (allFilled && code.length === 6) {
    error.value = null
    try {
      await auth.verifyA2F(code)
      
      // Si le requirea2f est false, rediriger vers dashboard'
      if (!auth.requires_a2f) {
        router.push({ name: 'home' })
      }
    } catch (e: any) {
      error.value = e?.message || t('a2f.invalidCode')
      // Vider les champs en cas d'erreur
      codeInputs.value = ['', '', '', '', '', '']
      await nextTick()
      inputRefs.value[0]?.focus()
    }
  }
}
</script>

<template>
  <div class="auth-shell">
    <!-- Colonne gauche : vérification A2F -->
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

        <div class="kicker mono">{{ t('a2f.kicker') }}</div>
        <h1>{{ t('a2f.title') }}</h1>
        <p class="lead">{{ t('a2f.lead') }}</p>

        <div v-if="error" class="error">
          <span class="mono">!</span>
          <span>{{ errorText }}</span>
        </div>

        <div class="code-inputs">
          <input
            v-for="(digit, index) in codeInputs"
            :key="index"
            :ref="(el) => inputRefs[index] = el as HTMLInputElement"
            type="text"
            class="code-box"
            maxlength="1"
            inputmode="numeric"
            pattern="[0-9]*"
            :value="digit"
            @input="onInput(index, $event)"
            @keydown="onKeydown(index, $event)"
            @paste="onPaste(index, $event)"
            autocomplete="off"
          >
        </div>

        <p class="info mono">
          {{ t('a2f.info1') }}
          <br/>
          {{ t('a2f.info2') }}
        </p>
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

/* ---------- Colonne gauche ---------- */
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

.code-inputs { display: flex; gap: 12px; margin-bottom: 24px; }
.code-box {
  width: 56px; height: 68px;
  font-size: 26px; font-weight: 600; text-align: center;
  background: var(--input-background);
  border: 1px solid var(--input-border);
  color: var(--white);
  transition: all 0.2s ease;
}
.code-box:focus {
  outline: none;
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 2px rgba(156, 77, 255, 0.18);
}

.error {
  background: rgba(255, 0, 46, 0.18);
  border-left: 3px solid var(--danger-color);
  padding: 10px 14px; font-size: 13px; margin-bottom: 24px;
  display: flex; gap: 10px; align-items: center; color: var(--white);
}
.error .mono { color: #ff6b6b; font-weight: 700; }
.info { font-size: 11px; color: var(--text-color-muted); margin: 0; line-height: 1.6; }

/* ---------- Colonne droite ---------- */
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