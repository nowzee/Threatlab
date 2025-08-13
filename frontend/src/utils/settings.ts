
/**
 * Types et interfaces pour les paramètres
 */
export interface PasswordChangeData {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export interface A2FActivationData {
  active: string;
  password: string;
  code?: string;
}

export interface A2FStatusResponse {
  success: boolean;
  active: boolean;
  error?: string;
}

export interface A2FActivationResponse {
  success: boolean;
  secret?: string;
  qrcode?: string;
  error?: string;
}

export interface ApiResponse {
  success: boolean;
  error?: string;
}

export interface PasswordStrengthConfig {
  minLength: number;
  levels: string[];
}

/**
 * Classe principale pour gérer les paramètres
 */
export class SettingsManager {
  private readonly passwordStrengthConfig: PasswordStrengthConfig = {
    minLength: 12,
    levels: ['weak', 'medium', 'strong']
  };

  private handlersInitialized = false;

  constructor() {
    this.init();
  }

  /**
   * Initialise le gestionnaire des paramètres
   */
  public init(): void {
    if (this.handlersInitialized) return;
    this.handlersInitialized = true;

    this.initPasswordHandlers();
    this.initA2FHandlers();
    this.initModalHandlers();
  }

  /**
   * Initialise les gestionnaires pour le changement de mot de passe
   */
  private initPasswordHandlers(): void {
    const passwordForm = document.getElementById('password-change-form') as HTMLFormElement;
    if (!passwordForm) return;

    // Ajouter les barres de robustesse du mot de passe
    this.initPasswordStrengthMeter();

    passwordForm.addEventListener('submit', (event) => this.handlePasswordChange(event));
  }

  /**
   * Initialise l'indicateur de robustesse du mot de passe
   */
  private initPasswordStrengthMeter(): void {
    const newPasswordInput = document.querySelector('input[name="new_password"]') as HTMLInputElement;
    if (!newPasswordInput || document.getElementById('password-strength')) return;

    const strengthContainer = document.createElement('div');
    strengthContainer.id = 'password-strength';
    strengthContainer.className = 'password-strength-meter';

    // Créer les trois barres
    for (let i = 0; i < 3; i++) {
      const bar = document.createElement('div');
      bar.className = 'strength-bar';
      bar.dataset.level = (i + 1).toString();
      strengthContainer.appendChild(bar);
    }

    newPasswordInput.parentNode?.insertBefore(strengthContainer, newPasswordInput.nextSibling);
    newPasswordInput.addEventListener('input', (event) => this.evaluatePasswordStrength(event));
  }

  /**
   * Gère la soumission du formulaire de changement de mot de passe
   */
  private async handlePasswordChange(event: Event): Promise<void> {
    event.preventDefault();

    const form = event.target as HTMLFormElement;
    const statusDiv = document.getElementById('password-status');
    const passwordInputs = form.querySelectorAll('input[type="password"]') as NodeListOf<HTMLInputElement>;

    if (passwordInputs.length < 3) {
      this.showStatus(statusDiv, 'Formulaire invalide', 'error');
      return;
    }

    const oldPassword = passwordInputs[0].value;
    const newPassword = passwordInputs[1].value;
    const confirmPassword = passwordInputs[2].value;

    // Validation côté client
    const validationError = this.validatePasswordChange({ old_password: oldPassword, new_password: newPassword, confirm_password: confirmPassword });
    if (validationError) {
      this.showStatus(statusDiv, validationError, 'error');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('old_password', oldPassword);
      formData.append('new_password', newPassword);
      formData.append('confirm_password', confirmPassword);

      const response = await fetch('/account/change-password', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
      });

      const data: ApiResponse = await response.json();

      if (data.success) {
        this.showStatus(statusDiv, 'Mot de passe modifié avec succès', 'success');
        this.resetPasswordForm(passwordInputs);
      } else {
        const errorMessage = data.error || 'Échec de la modification du mot de passe. Vérifiez votre mot de passe actuel.';
        this.showStatus(statusDiv, errorMessage, 'error');
      }
    } catch (error) {
      console.error('Erreur lors du changement de mot de passe:', error);
      this.showStatus(statusDiv, 'Une erreur est survenue. Veuillez réessayer.', 'error');
    }
  }

  /**
   * Valide les données de changement de mot de passe
   */
  private validatePasswordChange(data: PasswordChangeData): string | null {
    if (!data.old_password || !data.new_password || !data.confirm_password) {
      return 'Tous les champs sont obligatoires';
    }

    if (data.new_password !== data.confirm_password) {
      return 'Les nouveaux mots de passe ne correspondent pas';
    }

    if (data.new_password.length < this.passwordStrengthConfig.minLength) {
      return `Le mot de passe doit contenir au moins ${this.passwordStrengthConfig.minLength} caractères`;
    }

    if (data.new_password.length > 140) {
      return 'Le mot de passe ne doit pas dépasser 140 caractères';
    }

    const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*(),.?":{}|<>]).*$/;
    if (!passwordPattern.test(data.new_password)) {
      return 'Le mot de passe doit contenir au moins une lettre minuscule, une majuscule, un chiffre et un caractère spécial';
    }

    return null;
  }

  /**
   * Remet à zéro le formulaire de mot de passe
   */
  private resetPasswordForm(inputs: NodeListOf<HTMLInputElement>): void {
    inputs.forEach(input => {
      input.value = '';
    });

    const strengthMeter = document.getElementById('password-strength');
    if (strengthMeter) {
      const bars = strengthMeter.querySelectorAll('.strength-bar');
      bars.forEach(bar => bar.classList.remove('active'));
      strengthMeter.className = 'password-strength-meter';
    }
  }

  /**
   * Évalue la robustesse du mot de passe
   */
  private evaluatePasswordStrength(event: Event): void {
    const target = event.target as HTMLInputElement;
    const password = target.value;
    const strengthMeter = document.getElementById('password-strength');

    if (!strengthMeter) return;

    const bars = strengthMeter.querySelectorAll('.strength-bar');

    // Réinitialiser toutes les barres
    bars.forEach(bar => bar.classList.remove('active'));

    if (password.length === 0) {
      strengthMeter.className = 'password-strength-meter';
      return;
    }

    const strength = this.calculatePasswordStrength(password);

    for (let i = 0; i < strength; i++) {
      bars[i]?.classList.add('active');
    }

    strengthMeter.className = 'password-strength-meter';
    strengthMeter.classList.add(this.passwordStrengthConfig.levels[strength - 1]);
  }

  /**
   * Calcule la robustesse du mot de passe
   */
  private calculatePasswordStrength(password: string): number {
    const hasMinLength = password.length >= this.passwordStrengthConfig.minLength;
    const hasLowerCase = /[a-z]/.test(password);
    const hasUpperCase = /[A-Z]/.test(password);
    const hasNumbers = /[0-9]/.test(password);
    const hasSpecialChars = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    let score = 0;
    if (hasMinLength) score++;
    if (hasLowerCase && hasUpperCase) score++;
    if (hasNumbers) score++;
    if (hasSpecialChars) score++;

    if (score <= 1) return 1; // Faible
    if (score <= 3) return 2; // Moyen
    return 3; // Fort
  }

  /**
   * Initialise les gestionnaires pour l'authentification à deux facteurs
   */
  private initA2FHandlers(): void {
    this.checkA2FStatus();
    this.initA2FEventListeners();
  }

  /**
   * Initialise les événements A2F
   */
  private initA2FEventListeners(): void {
    const a2fVerificationSubmit = document.getElementById('a2f-verification-submit');
    const a2fActivateSubmit = document.getElementById('a2f-activate-submit');
    const a2fDeactivateSubmit = document.getElementById('a2f-deactivate-submit');

    a2fVerificationSubmit?.addEventListener('click', () => this.handleA2FVerification());
    a2fActivateSubmit?.addEventListener('click', () => this.handleA2FActivation());
    a2fDeactivateSubmit?.addEventListener('click', () => this.handleA2FDeactivation());
  }

  /**
   * Vérifie le statut A2F
   */
  private async checkA2FStatus(): Promise<void> {
    try {
      const response = await fetch('/account/check_a2f_status', {
        method: 'GET',
        credentials: 'same-origin'
      });

      const data: A2FStatusResponse = await response.json();
      if (data.success) {
        this.updateA2FInterface(data.active);
      }
    } catch (error) {
      console.error('Erreur lors de la vérification du statut A2F:', error);
    }
  }

  /**
   * Met à jour l'interface A2F
   */
  private updateA2FInterface(isActive: boolean): void {
    const statusIndicator = document.getElementById('a2f-status-indicator');
    const statusDot = statusIndicator?.querySelector('.status-dot') as HTMLElement;
    const statusText = document.getElementById('a2f-status-text');
    const toggleButton = document.getElementById('a2f-toggle-btn') as HTMLButtonElement;

    if (!statusIndicator || !statusText || !toggleButton) return;

    if (isActive) {
      statusIndicator.classList.add('status-active');
      statusIndicator.classList.remove('status-inactive');
      if (statusDot) statusDot.style.backgroundColor = '#00e676';
      statusText.textContent = 'Activée';
      toggleButton.textContent = 'Désactiver';
      toggleButton.classList.remove('btn-primary');
      toggleButton.classList.add('btn-danger');
    } else {
      statusIndicator.classList.add('status-inactive');
      statusIndicator.classList.remove('status-active');
      if (statusDot) statusDot.style.backgroundColor = '#cccccc';
      statusText.textContent = 'Désactivée';
      toggleButton.textContent = 'Activer';
      toggleButton.classList.remove('btn-danger');
      toggleButton.classList.add('btn-primary');
    }

    toggleButton.onclick = () => this.handleA2FToggle(isActive);
  }

  /**
   * Gère le basculement A2F
   */
  private handleA2FToggle(isActive: boolean): void {
    const modalId = isActive ? 'a2f-deactivate-modal' : 'a2f-activate-modal';
    const modal = document.getElementById(modalId);

    if (modal) {
      modal.style.display = 'block';
      this.clearModalInputs(modalId);
    }
  }

  /**
   * Vide les champs des modales
   */
  private clearModalInputs(modalId: string): void {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    const inputs = modal.querySelectorAll('input[type="password"], input[type="text"]') as NodeListOf<HTMLInputElement>;
    inputs.forEach(input => {
      input.value = '';
    });
  }

  /**
   * Gère la vérification du code A2F
   */
  private async handleA2FVerification(): Promise<void> {
    const codeInput = document.getElementById('a2f-verification-code') as HTMLInputElement;
    const statusDiv = document.getElementById('a2f-verification-status');

    if (!codeInput || !statusDiv) return;

    const code = codeInput.value.trim();

    if (!code) {
      this.showA2FStatus(statusDiv, 'Veuillez entrer le code généré par votre application', 'error');
      return;
    }

    if (code.length !== 6 || !/^\d+$/.test(code)) {
      this.showA2FStatus(statusDiv, 'Le code doit contenir 6 chiffres', 'error');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('code', code);

      const response = await fetch('/account/validation_a2f', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
      });

      const data: ApiResponse = await response.json();

      if (data.success) {
        this.showA2FStatus(statusDiv, 'Code validé avec succès! L\'authentification à deux facteurs est maintenant active.', 'success');
        this.checkA2FStatus();

        setTimeout(() => {
          const modal = document.getElementById('a2f-qrcode-modal');
          if (modal) modal.style.display = 'none';
        }, 1000);
      } else {
        this.showA2FStatus(statusDiv, data.error || 'Code incorrect. Veuillez réessayer.', 'error');
      }
    } catch (error) {
      console.error('Erreur lors de la validation du code:', error);
      this.showA2FStatus(statusDiv, 'Une erreur est survenue lors de la validation du code.', 'error');
    }
  }

  /**
   * Gère l'activation de l'A2F
   */
  private async handleA2FActivation(): Promise<void> {
    const passwordInput = document.getElementById('a2f-activate-password') as HTMLInputElement;
    if (!passwordInput) return;

    const password = passwordInput.value;
    if (!password) {
      alert('Veuillez entrer votre mot de passe');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('active', 'true');
      formData.append('password', password);

      const response = await fetch('/account/active_a2f', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
      });

      const data: A2FActivationResponse = await response.json();

      if (data.success && data.secret && data.qrcode) {
        const activateModal = document.getElementById('a2f-activate-modal');
        const qrcodeModal = document.getElementById('a2f-qrcode-modal');

        if (activateModal) activateModal.style.display = 'none';

        this.displayQRCode(data.secret, data.qrcode);

        if (qrcodeModal) qrcodeModal.style.display = 'block';
      } else {
        alert(data.error || 'Une erreur est survenue lors de l\'activation de l\'A2F');
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('Une erreur est survenue lors de la communication avec le serveur');
    }
  }

  /**
   * Affiche le QR code
   */
  private displayQRCode(secret: string, qrcodeData: string): void {
    const secretElement = document.getElementById('a2f-secret-key');
    const qrcodeContainer = document.getElementById('qrcode-container');

    if (secretElement) secretElement.textContent = secret;

    if (qrcodeContainer) {
      qrcodeContainer.innerHTML = '';
      const qrImage = document.createElement('img');
      qrImage.src = qrcodeData;
      qrImage.alt = 'QR Code pour authentification';
      qrImage.style.width = '200px';
      qrImage.style.height = '200px';
      qrcodeContainer.appendChild(qrImage);
    }
  }

  /**
   * Gère la désactivation de l'A2F
   */
  private async handleA2FDeactivation(): Promise<void> {
    const passwordInput = document.getElementById('a2f-deactivate-password') as HTMLInputElement;
    const codeInput = document.getElementById('a2f-deactivate-code') as HTMLInputElement;

    if (!passwordInput || !codeInput) return;

    const password = passwordInput.value;
    const code = codeInput.value;

    if (!password) {
      alert('Veuillez entrer votre mot de passe');
      return;
    }

    if (!code || code.length !== 6 || !/^\d+$/.test(code)) {
      alert('Veuillez entrer un code de vérification valide à 6 chiffres');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('active', 'false');
      formData.append('password', password);
      formData.append('code', code);

      const response = await fetch('/account/active_a2f', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
      });

      const data: ApiResponse = await response.json();

      if (data.success) {
        const modal = document.getElementById('a2f-deactivate-modal');
        if (modal) modal.style.display = 'none';

        alert('L\'authentification à deux facteurs a été désactivée avec succès');
        this.checkA2FStatus();
      } else {
        alert(data.error || 'Une erreur est survenue lors de la désactivation de l\'A2F');
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('Une erreur est survenue lors de la communication avec le serveur');
    }
  }

  /**
   * Initialise les gestionnaires de modales
   */
  private initModalHandlers(): void {
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.modal-close-btn, .close-btn');

    closeButtons.forEach(button => {
      button.addEventListener('click', this.closeModalHandler.bind(this));
    });

    modals.forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          (modal as HTMLElement).style.display = 'none';
        }
      });
    });
  }

  /**
   * Gestionnaire pour fermer les modales
   */
  private closeModalHandler(e: Event): void {
    e.preventDefault();
    e.stopPropagation();

    const modals = document.querySelectorAll('.modal') as NodeListOf<HTMLElement>;
    modals.forEach(modal => {
      modal.style.display = 'none';
    });
  }

  /**
   * Affiche un message d'état
   */
  private showStatus(element: HTMLElement | null, message: string, type: 'success' | 'error'): void {
    if (!element) return;

    element.textContent = message;
    element.style.color = type === 'success' ? '#00e676' : 'rgba(207,15,31,0.92)';
    element.className = 'form-status';
    element.classList.add(`status-${type}`);

    if (type === 'success') {
      setTimeout(() => {
        element.textContent = '';
        element.className = 'form-status';
      }, 5000);
    }
  }

  /**
   * Affiche un message d'état pour l'A2F
   */
  private showA2FStatus(element: HTMLElement | null, message: string, type: 'success' | 'error'): void {
    this.showStatus(element, message, type);
  }
}

// Export par défaut pour l'utilisation dans les composants Vue
export default SettingsManager;

// Instance globale pour la compatibilité avec l'ancienne approche
export const settingsManager = new SettingsManager();