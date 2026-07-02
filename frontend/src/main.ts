import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from '@/App.vue'
import router from './router'
import i18n from './i18n'
import { initTheme } from '@/utils/theme'

// CSS global
import '@/assets/css/variable.css'

// Apply the persisted (or system) theme and bind the OS-change listener.
initTheme()

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)

app.mount('#app')