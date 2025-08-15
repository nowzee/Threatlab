<script lang="ts" setup>
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const codeInputs = ref<string[]>(['', '', '', '', '', ''])
const inputRefs = ref<HTMLInputElement[]>([])
const error = ref<string | null>(null)

const router = useRouter()
const auth = useAuthStore()

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
    codeInputs.value[index + j] = digits[j]
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
      error.value = e?.message || 'Code de vérification invalide'
      // Vider les champs en cas d'erreur
      codeInputs.value = ['', '', '', '', '', '']
      await nextTick()
      inputRefs.value[0]?.focus()
    }
  }
}
</script>

<template>
  <div class="login-page">
  <div class="login-container">
    <div class="login-header">
      <h1 style="color: white">A2F Authentication</h1>
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
    <div class="login-form">
      <div class="form-group code-inputs">
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
    </div>
  </div>
  </div>
</template>

<style scoped src="@/assets/css/login.css"></style>