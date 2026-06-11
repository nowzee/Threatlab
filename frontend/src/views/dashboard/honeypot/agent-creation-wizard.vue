<script lang="ts">
import { defineComponent, ref, reactive, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

interface AgentTypeConfig {
  label: string
  defaultBanner: string
  defaultPort: number
  bannerLabel: string
  bannerHelp: string
  placeholderName: string
}

interface AgentConfig {
  name: string
  description: string
  ipAddress: string
  country: string
  banner: string
  networkConfig: {
    host: string
    port: number
    interface: string
  }
}

const AGENT_TYPE_CONFIGS: Record<string, AgentTypeConfig> = {
  ssh: {
    label: 'SSH',
    defaultBanner: 'SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5',
    defaultPort: 22,
    bannerLabel: 'Banniere SSH',
    bannerHelp: 'Banniere SSH affichee aux attaquants pour simuler un serveur specifique',
    placeholderName: 'Ex: SSH-Prod-01',
  },
  ftp: {
    label: 'FTP',
    defaultBanner: '220 FTP Server ready',
    defaultPort: 21,
    bannerLabel: 'Banniere FTP',
    bannerHelp: 'Banniere FTP affichee aux attaquants pour simuler un serveur specifique',
    placeholderName: 'Ex: FTP-Prod-01',
  }
}

export default defineComponent({
  name: "AgentCreationWizard",
  setup() {
    const route = useRoute()
    const router = useRouter()

    const agentType = computed(() => (route.params.type as string) || 'ssh')
    const typeConfig = computed((): AgentTypeConfig => {
      return AGENT_TYPE_CONFIGS[agentType.value] ?? AGENT_TYPE_CONFIGS['ssh']!
    })

    if (!AGENT_TYPE_CONFIGS[route.params.type as string]) {
      router.push({ name: 'deploy' })
    }

    const currentStep = ref(1)
    const totalSteps = 3
    const stepErrors = ref<string[]>([])

    const agentConfig = reactive<AgentConfig>({
      name: '',
      description: '',
      ipAddress: '',
      country: '',
      banner: typeConfig.value.defaultBanner,
      networkConfig: {
        host: '0.0.0.0',
        port: typeConfig.value.defaultPort,
        interface: 'eth0'
      }
    })

    watch(agentType, () => {
      const cfg = AGENT_TYPE_CONFIGS[agentType.value]
      if (cfg) {
        agentConfig.banner = cfg.defaultBanner
        agentConfig.networkConfig.port = cfg.defaultPort
      }
    })

    const isSubmitting = ref(false)
    const createdAgentId = ref<number | null>(null)
    const copiedCommand = ref<string | null>(null)
    const serverUrl = window.location.origin

    const steps = [
      { number: 1, title: 'Informations' },
      { number: 2, title: 'Reseau' },
      { number: 3, title: 'Deploiement' },
    ]

    const validateStep = (step: number): boolean => {
      stepErrors.value = []
      if (step === 1) {
        if (!agentConfig.name.trim()) stepErrors.value.push('Le nom de l\'agent est obligatoire')
        if (!agentConfig.description.trim()) stepErrors.value.push('La description est obligatoire')
      }
      if (step === 2) {
        if (agentConfig.networkConfig.port < 1 || agentConfig.networkConfig.port > 65535) {
          stepErrors.value.push('Le port doit etre entre 1 et 65535')
        }
      }
      return stepErrors.value.length === 0
    }

    const nextStep = () => {
      if (validateStep(currentStep.value) && currentStep.value < totalSteps) {
        currentStep.value++
      }
    }

    const prevStep = () => {
      if (currentStep.value > 1) {
        stepErrors.value = []
        currentStep.value--
      }
    }

    const goToStep = (step: number) => {
      if (createdAgentId.value) return
      if (step < currentStep.value) {
        stepErrors.value = []
        currentStep.value = step
      }
    }

    const getStepState = (step: number) => {
      if (step === currentStep.value) return 'active'
      if (step < currentStep.value) return 'completed'
      return 'upcoming'
    }

    const createAgent = async () => {
      isSubmitting.value = true
      stepErrors.value = []
      try {
        const response = await fetch('/api/agent/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            agent_name: agentConfig.name,
            agent_type: agentType.value,
            ip_address: agentConfig.ipAddress || '0.0.0.0',
            country_name: agentConfig.country,
            banner: agentConfig.banner
          })
        })
        const data = await response.json()
        if (response.ok && data.success) {
          createdAgentId.value = data.agent_id
        } else {
          stepErrors.value = [data.error || 'Erreur lors de la creation']
        }
      } catch {
        stepErrors.value = ['Erreur de connexion au serveur']
      } finally {
        isSubmitting.value = false
      }
    }

    const getInstallCommand = (method: string) => {
      if (!createdAgentId.value) return ''
      const base = `curl -sSL ${serverUrl}/api/agent/install/${createdAgentId.value} | sudo bash`
      if (method === 'interactive') return base
      return `${base} -s -- --method ${method}`
    }

    const copyCommand = async (method: string) => {
      const cmd = getInstallCommand(method)
      try {
        await navigator.clipboard.writeText(cmd)
      } catch {
        const ta = document.createElement('textarea')
        ta.value = cmd
        document.body.appendChild(ta)
        ta.select()
        document.execCommand('copy')
        document.body.removeChild(ta)
      }
      copiedCommand.value = method
      setTimeout(() => { copiedCommand.value = null }, 2000)
    }

    const downloadAgent = () => {
      if (createdAgentId.value) {
        window.location.href = `/api/agent/download/${createdAgentId.value}`
      }
    }

    const goBack = () => { router.push({ name: 'deploy' }) }

    return {
      agentType, typeConfig, currentStep, totalSteps, steps, stepErrors,
      agentConfig, isSubmitting, createdAgentId, copiedCommand,
      getStepState, nextStep, prevStep, goToStep,
      createAgent, getInstallCommand, copyCommand, downloadAgent, goBack
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <!-- Header -->
    <div class="wizard-header">
      <button class="btn btn-secondary" @click="goBack">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
        Retour
      </button>
      <h1 class="page-title">Creer un Agent {{ typeConfig.label }}</h1>
    </div>

    <!-- Progress -->
    <div class="wizard-progress">
      <div v-for="(step, index) in steps" :key="step.number" class="wizard-step-item" :class="getStepState(step.number)" @click="goToStep(step.number)">
        <div class="step-circle">
          <svg v-if="getStepState(step.number) === 'completed'" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
          <span v-else>{{ step.number }}</span>
        </div>
        <span class="step-label">{{ step.title }}</span>
        <div v-if="index < steps.length - 1" class="step-connector"></div>
      </div>
    </div>

    <!-- Errors -->
    <div v-if="stepErrors.length > 0" class="wizard-errors">
      <div v-for="(err, i) in stepErrors" :key="i" class="error-item">{{ err }}</div>
    </div>

    <div class="wizard-content">
      <!-- Step 1: Basic Info -->
      <div v-if="currentStep === 1" class="section-card">
        <div class="card-header"><h3 class="card-title">Informations de base</h3></div>
        <div class="card-body">
          <div class="form-grid">
            <div class="form-group">
              <label for="agent-name">Nom de l'agent *</label>
              <input id="agent-name" v-model="agentConfig.name" type="text" class="form-input" :placeholder="typeConfig.placeholderName" />
            </div>
            <div class="form-group">
              <label for="agent-ip">Adresse IP / Domaine</label>
              <input id="agent-ip" v-model="agentConfig.ipAddress" type="text" class="form-input" placeholder="Ex: 203.0.113.50" />
            </div>
            <div class="form-group">
              <label for="agent-country">Pays de deploiement</label>
              <input id="agent-country" v-model="agentConfig.country" type="text" class="form-input" placeholder="Ex: France" />
            </div>
            <div class="form-group full-width">
              <label for="agent-description">Description *</label>
              <textarea id="agent-description" v-model="agentConfig.description" class="form-input" rows="3" placeholder="Description de l'agent et de son role"></textarea>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 2: Network -->
      <div v-if="currentStep === 2" class="section-card">
        <div class="card-header"><h3 class="card-title">Configuration reseau</h3></div>
        <div class="card-body">
          <div class="form-grid">
            <div class="form-group full-width">
              <label for="agent-banner">{{ typeConfig.bannerLabel }}</label>
              <input id="agent-banner" v-model="agentConfig.banner" type="text" class="form-input" :placeholder="typeConfig.defaultBanner" />
              <small class="form-help">{{ typeConfig.bannerHelp }}</small>
            </div>
            <div class="form-group">
              <label for="network-host">Adresse d'ecoute</label>
              <input id="network-host" v-model="agentConfig.networkConfig.host" type="text" class="form-input" placeholder="0.0.0.0" />
            </div>
            <div class="form-group">
              <label for="network-port">Port</label>
              <input id="network-port" v-model.number="agentConfig.networkConfig.port" type="number" class="form-input" min="1" max="65535" />
            </div>
            <div class="form-group">
              <label for="network-interface">Interface reseau</label>
              <input id="network-interface" v-model="agentConfig.networkConfig.interface" type="text" class="form-input" placeholder="eth0" />
            </div>
          </div>
        </div>
      </div>

      <!-- Step 3: Review & Deploy -->
      <div v-if="currentStep === 3">
        <!-- Pre-creation: Review -->
        <div v-if="!createdAgentId" class="section-card">
          <div class="card-header"><h3 class="card-title">Resume de la configuration</h3></div>
          <div class="card-body">
            <div class="review-section">
              <h4 class="review-section-title">Informations</h4>
              <div class="review-grid">
                <div class="review-item"><span class="review-label">Nom</span><span class="review-value">{{ agentConfig.name }}</span></div>
                <div class="review-item"><span class="review-label">Type</span><span class="review-value badge-type">{{ typeConfig.label }}</span></div>
                <div class="review-item"><span class="review-label">IP</span><code class="review-value">{{ agentConfig.ipAddress || '0.0.0.0' }}</code></div>
                <div class="review-item"><span class="review-label">Pays</span><span class="review-value">{{ agentConfig.country || 'Non defini' }}</span></div>
                <div class="review-item full-width"><span class="review-label">Description</span><span class="review-value">{{ agentConfig.description }}</span></div>
              </div>
            </div>
            <div class="review-section">
              <h4 class="review-section-title">Reseau</h4>
              <div class="review-grid">
                <div class="review-item"><span class="review-label">Port</span><code class="review-value">{{ agentConfig.networkConfig.port }}</code></div>
                <div class="review-item"><span class="review-label">Host</span><code class="review-value">{{ agentConfig.networkConfig.host }}</code></div>
                <div class="review-item"><span class="review-label">Interface</span><code class="review-value">{{ agentConfig.networkConfig.interface }}</code></div>
                <div class="review-item full-width"><span class="review-label">Banniere</span><code class="review-value review-banner">{{ agentConfig.banner }}</code></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Post-creation: Deploy -->
        <div v-if="createdAgentId" class="section-card deploy-card">
          <h4 class="deploy-title">Methodes d'installation</h4>

          <div v-for="m in [
            { key: 'docker', name: 'Docker', tag: 'Recommande' },
            { key: 'direct', name: 'Direct (systemd)', tag: '' },
            { key: 'manual', name: 'Manuel', tag: '' }
          ]" :key="m.key" class="deploy-method">
            <div class="method-top">
              <div class="method-info">
                <span class="method-name">{{ m.name }}</span>
                <span v-if="m.tag" class="method-tag">{{ m.tag }}</span>
              </div>
              <button class="btn-copy" @click="copyCommand(m.key)">
                {{ copiedCommand === m.key ? 'Copie !' : 'Copier' }}
              </button>
            </div>
            <code class="method-cmd">{{ getInstallCommand(m.key) }}</code>
          </div>

          <div class="deploy-actions">
            <button class="btn btn-secondary" @click="downloadAgent">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              Telecharger le script
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <div class="wizard-nav">
      <button v-if="currentStep > 1 && !createdAgentId" class="btn btn-secondary" @click="prevStep">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
        Precedent
      </button>
      <div class="nav-spacer"></div>
      <button v-if="currentStep < totalSteps && !createdAgentId" class="btn btn-primary" @click="nextStep">
        Suivant
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
      </button>
      <button v-if="currentStep === totalSteps && !createdAgentId" class="btn btn-primary btn-create" @click="createAgent" :disabled="isSubmitting">
        {{ isSubmitting ? 'Creation...' : 'Creer l\'agent' }}
      </button>
      <button v-if="createdAgentId" class="btn btn-primary" @click="goBack">Terminer</button>
    </div>
  </div>
</template>

<style scoped>
.wizard-header { display: flex; align-items: center; gap: 16px; margin-bottom: 32px; }

/* Progress */
.wizard-progress { display: flex; align-items: center; justify-content: center; margin-bottom: 40px; }
.wizard-step-item { display: flex; align-items: center; cursor: pointer; transition: all 0.2s; }
.wizard-step-item.upcoming { cursor: default; }

.step-circle {
  width: 40px; height: 40px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 15px; flex-shrink: 0; transition: all 0.3s;
}
.wizard-step-item.upcoming .step-circle { background: var(--card-background); border: 2px solid var(--container-border-color); color: #666; }
.wizard-step-item.active .step-circle { background: var(--accent-color); border: 2px solid var(--accent-color); color: #fff; box-shadow: 0 0 20px rgba(156, 77, 255, 0.3); }
.wizard-step-item.completed .step-circle { background: var(--success-color); border: 2px solid var(--success-color); color: #fff; }

.step-label { margin-left: 10px; font-size: 14px; font-weight: 600; white-space: nowrap; }
.wizard-step-item.upcoming .step-label { color: #555; }
.wizard-step-item.active .step-label { color: var(--white); }
.wizard-step-item.completed .step-label { color: var(--success-color); }

.step-connector { width: 60px; height: 2px; margin: 0 16px; background: var(--container-border-color); flex-shrink: 0; }
.wizard-step-item.completed .step-connector { background: var(--success-color); }

/* Errors */
.wizard-errors { max-width: 800px; margin: 0 auto 24px; }
.error-item {
  padding: 10px 16px; background: rgba(194, 42, 55, 0.1);
  border: 1px solid rgba(194, 42, 55, 0.3); border-radius: 8px;
  color: #ff5252; font-size: 14px; margin-bottom: 8px;
}

/* Content */
.wizard-content { max-width: 800px; margin: 0 auto; }

/* Forms */
.form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 8px; }
.form-group.full-width { grid-column: 1 / -1; }
.form-group label { font-weight: 600; color: var(--white); font-size: 14px; }
.form-input {
  padding: 12px; border: 1px solid var(--container-border-color); border-radius: 8px;
  background: #111; color: var(--white); font-size: 14px; transition: border-color 0.2s, box-shadow 0.2s;
}
.form-input:focus { outline: none; border-color: var(--accent-color); box-shadow: 0 0 0 3px rgba(156, 77, 255, 0.1); }
.form-help { color: var(--text-color-muted); font-size: 12px; }

/* Review */
.review-section { margin-bottom: 28px; }
.review-section:last-child { margin-bottom: 0; }
.review-section-title {
  font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;
  color: var(--accent-color); margin: 0 0 14px; padding-bottom: 10px; border-bottom: 1px solid var(--container-border-color);
}
.review-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.review-item { display: flex; flex-direction: column; gap: 4px; }
.review-item.full-width { grid-column: 1 / -1; }
.review-label { font-size: 12px; color: var(--text-color-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; }
.review-value { font-size: 14px; color: var(--white); font-weight: 500; }
.review-banner { font-size: 12px; }
.badge-type {
  display: inline-block; padding: 2px 10px; background: rgba(30, 84, 229, 0.2);
  color: #42a5f5; border-radius: 6px; font-size: 13px; font-weight: 700; width: fit-content;
}

/* Deploy */
.deploy-card { padding: 28px; }
.deploy-title { font-size: 15px; font-weight: 700; color: var(--white); margin: 0 0 16px; }
.deploy-method {
  margin-bottom: 14px; background: #0d0d0d; border-radius: 10px;
  padding: 14px 16px; border: 1px solid var(--container-border-color);
}
.method-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.method-info { display: flex; align-items: center; gap: 10px; }
.method-name { font-size: 14px; font-weight: 600; color: #ccc; }
.method-tag {
  font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 4px;
  text-transform: uppercase; background: rgba(156, 77, 255, 0.15); color: var(--accent-color);
}
.btn-copy {
  background: rgba(156, 77, 255, 0.12); border: 1px solid rgba(156, 77, 255, 0.25);
  color: var(--accent-color); padding: 5px 14px; border-radius: 6px;
  font-size: 12px; font-weight: 600; cursor: pointer; transition: background 0.2s;
}
.btn-copy:hover { background: rgba(156, 77, 255, 0.22); }
.method-cmd {
  display: block; font-size: 11px; color: #999; word-break: break-all;
  line-height: 1.6; font-family: 'JetBrains Mono', 'Fira Code', monospace;
}
.deploy-actions { margin-top: 20px; display: flex; gap: 12px; }

/* Navigation */
.wizard-nav {
  max-width: 800px; margin: 32px auto 0; display: flex; align-items: center;
  padding: 20px 0; border-top: 1px solid var(--container-border-color);
}
.nav-spacer { flex: 1; }
.btn-create { padding: 12px 32px; }

/* Responsive */
@media (max-width: 768px) {
  .wizard-progress { flex-wrap: wrap; gap: 8px; }
  .step-connector { width: 30px; margin: 0 8px; }
  .step-label { display: none; }
  .form-grid, .review-grid { grid-template-columns: 1fr; }
}
</style>
