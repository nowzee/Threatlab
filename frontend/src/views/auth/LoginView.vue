<script lang="ts" setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const username = ref('')
const password = ref('')

const router = useRouter()
const auth = useAuthStore()

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
  <div class="login-page">
     <div class="login-container">
        <div class="login-header">
            <h1 style="color: white">Connexion</h1>
            <div v-if="auth.error" class="error-message">
                {{ auth.error }}
            </div>
        </div>
        <form class="login-form" @submit.prevent="onSubmit">
            <div class="form-group">
                <label style="color: white" for="username">Username</label>
                <input type="text" id="username" v-model="username" name="username" placeholder="Username" required>
            </div>
            <div class="form-group">
                <label style="color: white" for="password">Password</label>
                <input type="password" id="password" v-model="password" name="password" placeholder="Password" required>
            </div>
            <div class="form-group">
                <button type="submit">Signin</button>
            </div>
        </form>
    </div>
  </div>
</template>

<style scoped src="@/assets/css/login.css"></style>
