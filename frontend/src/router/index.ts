
import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/auth/LoginView.vue'
import A2FView from '@/views/auth/a2f.vue'

import DashboardView from '@/views/DashboardView.vue'
import home from '@/views/dashboard/home.vue'
import deploy from '@/views/dashboard/deploy.vue'
import agentCreation from '@/views/dashboard/agent-creation.vue'
import threatIntel from '@/views/dashboard/threat-intel.vue'
import alerts from '@/views/dashboard/alerts.vue'
import alertDetails from '@/views/dashboard/alert-details.vue'
import honeypotManagement from '@/views/dashboard/honeypot-management.vue'
import settings from '@/views/dashboard/settings/settings.vue'
import security_settings from "@/views/dashboard/settings/security.vue";
import api_settings from "@/views/dashboard/settings/api.vue";


const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView,
    meta: { public: false },
    children: [
      { path: '', redirect: { name: 'home' } },
      { path: 'home', name: 'home', component: home },
      { path: 'deploy', name: 'deploy', component: deploy },
      { path: 'agent-creation', name: 'agent-creation', component: agentCreation },
      { path: 'honeypot-management', name: 'honeypot-management', component: honeypotManagement },
      { path: 'threat-intel', name: 'threat-intel', component: threatIntel },
      { path: 'alerts', name: 'alerts', component: alerts },
      { path: 'alert-details/:id', name: 'alert-details', component: alertDetails },
      { path: 'settings', name: 'settings', component: settings,
      children: [
          { path: '', redirect: { name: 'security_settings' } },
          { path: 'security', name: 'security_settings', component: security_settings },
          { path: 'api', name: 'api_settings', component: api_settings}
      ]},
    ],
  },
  { path: '/a2f', name: 'a2f', component: A2FView, meta: { public: true } },

  // Route catch-all dynamique basée sur l'authentification
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: () => {
      const auth = useAuthStore()

      // Si authentifié et pas d'A2F requis, aller vers home
      if (auth.isAuthenticated && !auth.requires_a2f) {
        return { name: 'home' }
      }

      // Si A2F requis, aller vers A2F
      if (auth.requires_a2f) {
        return { name: 'a2f' }
      }

      // Sinon aller vers login
      return { name: 'login' }
    }
  },
]



const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

let isCheckingAuth = false; // Prévenir les appels multiples

router.beforeEach(async (to, from) => {
  // Éviter les appels répétitifs
  if (isCheckingAuth) {
    return true;
  }

  const auth = useAuthStore()

  // Ne vérifier la session que si nécessaire
  if (!auth.hasCheckedSession) {
    isCheckingAuth = true;
    try {
      await auth.fetchSession(true)
    } finally {
      isCheckingAuth = false;
    }
  }

  if (to.name === 'login' && auth.isAuthenticated) {
      return auth.requires_a2f ? { name: 'a2f' } : { name: 'home' }
  }

  // Si on essaie d'accéder à A2F mais pas d'A2F requis
  if (to.name === 'a2f' && !auth.requires_a2f) {
    return auth.isAuthenticated ? { name: 'home' } : { name: 'login' }
  }

  // Vérifier les routes protégées
  if (!to.meta.public) {
    // Si A2F requis, rediriger vers A2F
    if (auth.requires_a2f) {
      return { name: 'a2f' }
    }
    // Si pas authentifié du tout, rediriger vers login
    if (!auth.isAuthenticated) {
      return { name: 'login'}
    }
  }

  return true
})

export default router