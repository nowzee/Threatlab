
import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/auth/LoginView.vue'
import A2FView from '@/views/auth/a2f.vue'

import DashboardView from '@/views/DashboardView.vue'
import home from '@/views/dashboard/home.vue'
import deploy from '@/views/dashboard/honeypot/deploy.vue'
import agentCreationWizard from '@/views/dashboard/honeypot/agent-creation-wizard.vue'
import threatIntel from '@/views/dashboard/CTI/threat-intel.vue'
import alerts from '@/views/dashboard/alert/alerts.vue'
import alertDetails from '@/views/dashboard/alert/alert-details.vue'
import honeypotManagement from '@/views/dashboard/honeypot/honeypot-management.vue'
import honeypotDetail from '@/views/dashboard/honeypot/honeypot-detail.vue'
import settings from '@/views/dashboard/settings/settings.vue'
import security_settings from "@/views/dashboard/settings/security.vue";
import api_settings from "@/views/dashboard/settings/api.vue";
import appearance_settings from "@/views/dashboard/settings/appearance.vue";
import wordlists from "@/views/dashboard/wordlists/wordlists.vue"
import payloads from "@/views/dashboard/payloads/payloads.vue"
import adminUsers from "@/views/dashboard/admin/users.vue"
import adminAudit from "@/views/dashboard/admin/audit.vue"


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
        { path: 'agent-creation/:type', name: 'agent-creation', component: agentCreationWizard },
        { path: 'honeypot-management', name: 'honeypot-management', component: honeypotManagement },
        { path: 'honeypot-management/honeypot-detail/:id', name: 'honeypot-detail', component: honeypotDetail },
        { path: 'threat-intel', name: 'threat-intel', component: threatIntel },
        { path: 'alerts', name: 'alerts', component: alerts },
        { path: 'alert-details/:id', name: 'alert-details', component: alertDetails },
        { path: 'wordlists', name: 'wordlists', component: wordlists },
        { path: 'payloads', name: 'payloads', component: payloads },
        { path: 'admin/users', name: 'admin-users', component: adminUsers, meta: { requiresAdmin: true } },
        { path: 'admin/audit', name: 'admin-audit', component: adminAudit, meta: { requiresAdmin: true } },
        { path: 'settings', name: 'settings', component: settings,
        children: [
            { path: '', redirect: { name: 'security_settings' } },
            { path: 'security', name: 'security_settings', component: security_settings },
            { path: 'api', name: 'api_settings', component: api_settings},
            { path: 'appearance', name: 'appearance_settings', component: appearance_settings}
        ]},
        ],
    },
  { path: '/a2f', name: 'a2f', component: A2FView, meta: { public: true } },

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

  // Routes réservées aux administrateurs
  if (to.meta.requiresAdmin && auth.user?.role !== 'admin') {
    return { name: 'home' }
  }

  return true
})

export default router