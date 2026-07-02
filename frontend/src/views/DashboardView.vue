<script lang="ts">
import { defineComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from "@/stores/auth.ts";

export default defineComponent({
  name: "DashboardView",
  setup() {
    const route = useRoute()
    const router = useRouter()
    const auth = useAuthStore()

    const onSubmit = async () => {
      await auth.logout()
      await router.push({ name: 'login' });
    }
    const navigateTo = (path: string) => {
      router.push(path)
    }

    return {
      route,
      auth,
      onSubmit,
      navigateTo
    }
  }
})
</script>


<template>
    <!-- Sidebar / Menu latéral -->
  <div class="container-fluid">
    <div class="container-sidebar">
        <div class="sidebar-header">
            <div class="sidebar-logo">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="sidebar-logo-icon">
                    <path d="M16 16v1a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2m5.66 0H14a2 2 0 0 1 2 2v3.34"></path>
                    <path d="M3 15h3m9-3h3"></path>
                    <path d="M21 14a3 3 0 1 1-3 3v-1"></path>
                    <path d="M14 7V5a3 3 0 0 1 3-3l4 9-8 11z"></path>
                </svg>
                Threatlab
            </div>
        </div>

        <div class="sidebar-section">
            <div class="sidebar-section-title">Général</div>
            <a
                class="btn-sidebar"
                :class="{ active: route.path === '/dashboard/home' }"
                id="dashboard-btn"
                @click="navigateTo('/dashboard/home')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="7" height="7"></rect>
                    <rect x="14" y="3" width="7" height="7"></rect>
                    <rect x="14" y="14" width="7" height="7"></rect>
                    <rect x="3" y="14" width="7" height="7"></rect>
                </svg>
                <span>Tableau de bord</span>
            </a>
        </div>

        <div class="sidebar-section">
            <div class="sidebar-section-title">Honeypots</div>
            <a
                class="btn-sidebar"
                :class="{ active: route.path === '/dashboard/deploy' }"
                id="deploy-btn"
                @click="navigateTo('/dashboard/deploy')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"></path>
                </svg>
                <span>Déployer un honeypot</span>
            </a>
            <a
                class="btn-sidebar"
                :class="{ active: route.path.startsWith('/dashboard/honeypot-management') }"
                id="manage-btn"
                @click="navigateTo('/dashboard/honeypot-management')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 11V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h6"></path>
                    <path d="M12 16H7"></path>
                    <path d="M12 12H7"></path>
                    <path d="M12 8H7"></path>
                    <path d="M16 16v6"></path>
                    <path d="M19 19l-3-3-3 3"></path>
                </svg>
                <span>Gérer les honeypots</span>
            </a>
        </div>

        <div class="sidebar-section">
            <div class="sidebar-section-title">Analyse</div>
            <a 
                class="btn-sidebar" 
                :class="{ active: route.path === '/dashboard/alerts' }"
                id="alerts-btn"
                @click="navigateTo('/dashboard/alerts')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                    <line x1="12" y1="9" x2="12" y2="13"></line>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                <span>Alertes</span>
            </a>
            <a 
                class="btn-sidebar"
                :class="{ active: route.path === '/dashboard/threat-intel' }"
                id="CTI-btn"
                @click="navigateTo('/dashboard/threat-intel')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                <span>Threat Intelligence</span>
            </a>
          <a
                class="btn-sidebar"
                :class="{ active: route.path === '/dashboard/wordlists' }"
                @click="navigateTo('/dashboard/wordlists')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                <span>Wordlists</span>
            </a>
          <a
                class="btn-sidebar"
                :class="{ active: route.path === '/dashboard/payloads' }"
                @click="navigateTo('/dashboard/payloads')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                </svg>
                <span>Payloads &amp; Commandes</span>
            </a>
        </div>

        <div class="sidebar-section" v-if="auth.user?.role === 'admin'">
            <div class="sidebar-section-title">Administration</div>
            <a
                class="btn-sidebar"
                :class="{ active: route.path === '/dashboard/admin/users' }"
                id="admin-users-btn"
                @click="navigateTo('/dashboard/admin/users')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
                <span>Utilisateurs</span>
            </a>
            <a
                class="btn-sidebar"
                :class="{ active: route.path === '/dashboard/admin/audit' }"
                id="admin-audit-btn"
                @click="navigateTo('/dashboard/admin/audit')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2"></rect>
                    <line x1="7" y1="8" x2="17" y2="8"></line>
                    <line x1="7" y1="12" x2="17" y2="12"></line>
                    <line x1="7" y1="16" x2="13" y2="16"></line>
                </svg>
                <span>Journaux d'audit</span>
            </a>
        </div>

        <div class="sidebar-section">
            <div class="sidebar-section-title">Systeme</div>
            <a
                class="btn-sidebar"
                :class="{ active: route.path.startsWith('/dashboard/settings')}"
                id="config-btn"
                @click="navigateTo('/dashboard/settings')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                </svg>
                <span>Paramètres</span>
            </a>
        </div>

        <div class="sidebar-footer">
            <div class="user-profile">
                <div class="user-avatar">{{ (auth.user?.username || 'U').charAt(0).toUpperCase() }}</div>
                <div class="user-info">
                    <div class="user-name">{{ auth.user?.username || 'Utilisateur' }}</div>
                    <div class="user-role">{{ auth.user?.role === 'admin' ? 'Administrateur' : 'Membre' }}</div>
                </div>
            </div>
            <a @click="onSubmit" class="btn-icon btn-secondary" id="deconnexion" style="margin-bottom: 10px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                    <polyline points="16 17 21 12 16 7"></polyline>
                    <line x1="21" y1="12" x2="9" y2="12"></line>
                </svg>
            </a>
        </div>
    </div>
    <div class="container-main">
        <router-view />
    </div>
  </div>
</template>

<style src="@/assets/css/components.css"></style>
<style src="@/assets/css/dashboard/base.css"></style>
<style src="@/assets/css/dashboard/modal.css"></style>
<style src="@/assets/css/dashboard/sidebar.css"></style>