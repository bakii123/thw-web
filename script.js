class SoulCompanion {
    constructor() {
        this.currentUser = null;
        this.messages = [];
        this.isLoggedIn = false;
        this.phase = null; // 'questioning', 'advice', or 'paywall'
        this.intakeAnswers = [];
        this.intakeIndex = 0;
        this.guestId = this.ensureGuestId();
        this.language = this.getLanguage();
        this.translations = {};
        this.hasPaywallTriggered = false;
        
        this.initElements();
        this.bindEvents();
        this.loadTranslations();
        this.recoverSession();
        this.checkAuthStatus();
    }
    
    getLanguage() {
        let lang = localStorage.getItem('soul_companion_language');
        if (!lang || !['en', 'ar', 'fr'].includes(lang)) {
            lang = 'en';
            localStorage.setItem('soul_companion_language', lang);
        }
        return lang;
    }
    
    // Save entire session to localStorage
    saveSession() {
        const sessionData = {
            messages: this.messages,
            phase: this.phase,
            intakeAnswers: this.intakeAnswers,
            intakeIndex: this.intakeIndex,
            language: this.language,
            hasPaywallTriggered: this.hasPaywallTriggered,
            timestamp: Date.now()
        };
        localStorage.setItem('soul_companion_session', JSON.stringify(sessionData));
    }
    
    // Recover session from localStorage
    recoverSession() {
        const sessionData = localStorage.getItem('soul_companion_session');
        if (sessionData) {
            try {
                const data = JSON.parse(sessionData);
                // Only restore if session is less than 24 hours old
                if (Date.now() - data.timestamp < 86400000) {
                    this.messages = data.messages || [];
                    this.phase = data.phase;
                    this.intakeAnswers = data.intakeAnswers || [];
                    this.intakeIndex = data.intakeIndex || 0;
                    this.language = data.language || 'en';
                    this.hasPaywallTriggered = data.hasPaywallTriggered || false;
                    
                    localStorage.setItem('soul_companion_language', this.language);
                    
                    // Restore UI
                    this.restoreChatHistory();
                }
            } catch (e) {
                console.error('Failed to recover session:', e);
            }
        }
    }
    
    // Restore chat messages to the UI
    restoreChatHistory() {
        this.messagesContainer.innerHTML = '';
        this.messages.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${msg.sender}`;
            messageDiv.innerHTML = `
                <div class="message-content">${this.formatMessage(msg.text)}</div>
                <div class="message-time">${msg.time}</div>
            `;
            this.messagesContainer.appendChild(messageDiv);
        });
        this.scrollToBottom();
    }
    
    async loadTranslations() {
        try {
            const resp = await fetch(`/api/translations/${this.language}`);
            const data = await resp.json();
            this.translations = data.translations;
            this.updateUIText();
        } catch (e) {
            console.error('Failed to load translations:', e);
        }
    }
    
    updateUIText() {
        // Update modal header
        document.getElementById('appTitle').textContent = this.t('app_title');
        document.getElementById('tagline').textContent = this.t('tagline');
        
        // Update tabs
        document.getElementById('loginTabBtn').textContent = this.t('login');
        document.getElementById('signupTabBtn').textContent = this.t('signup');
        
        // Update buttons
        document.getElementById('loginBtn').textContent = this.t('enter');
        document.getElementById('registerBtn').textContent = this.t('create_account');
        document.getElementById('logoutBtn').textContent = this.t('logout');
        document.getElementById('upgradeBtn').textContent = this.t('upgrade');
        
        // Update placeholders
        document.getElementById('loginUsername').placeholder = 'Username';
        document.getElementById('loginPassword').placeholder = this.t('login');
        document.getElementById('registerUsername').placeholder = this.t('create_account');
        document.getElementById('registerPassword').placeholder = this.t('create_account');
        document.getElementById('messageInput').placeholder = this.t('share');
        
        // Update username display if guest
        if (!this.currentUser) {
            document.getElementById('usernameDisplay').textContent = this.t('guest');
        }
    }
    
    t(key) {
        return this.translations[key] || key;
    }
    
    initElements() {
        this.authModal = document.getElementById('authModal');
        this.chatContainer = document.getElementById('chatContainer');
        this.loginForm = document.getElementById('loginForm');
        this.registerForm = document.getElementById('registerForm');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.messagesContainer = document.getElementById('messages');
        this.usernameDisplay = document.getElementById('usernameDisplay');
        this.upgradeBtn = document.getElementById('upgradeBtn');
        this.logoutBtn = document.getElementById('logoutBtn');
        this.inputStatus = document.getElementById('inputStatus');
        
        // Tab buttons
        this.tabBtns = document.querySelectorAll('.tab-btn');
        this.authForms = document.querySelectorAll('.auth-form');
        
        // Language buttons
        this.langBtns = document.querySelectorAll('.lang-btn');
    }
    
    bindEvents() {
        // Auth tabs
        this.tabBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                this.switchTab(tab);
            });
        });
        
        // Language buttons
        this.langBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.changeLanguage(e.target.dataset.lang);
            });
        });
        
        // Forms
        this.loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        this.registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        
        // Chat
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.logoutBtn.addEventListener('click', () => this.logout());
        this.upgradeBtn.addEventListener('click', () => this.showUpgrade());
    }
    
    changeLanguage(lang) {
        if (['en', 'ar', 'fr'].includes(lang)) {
            this.language = lang;
            localStorage.setItem('soul_companion_language', lang);
            this.loadTranslations();
            this.saveSession();
            
            // Update active button
            this.langBtns.forEach(btn => {
                if (btn.dataset.lang === lang) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
            
            // Update document direction for Arabic
            if (lang === 'ar') {
                document.body.style.direction = 'rtl';
                document.body.style.textAlign = 'right';
            } else {
                document.body.style.direction = 'ltr';
                document.body.style.textAlign = 'left';
            }
        }
    }
    
    switchTab(tabName) {
        this.tabBtns.forEach(btn => btn.classList.remove('active'));
        this.authForms.forEach(form => form.classList.remove('active'));
        
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(tabName === 'login' ? 'loginForm' : 'registerForm').classList.add('active');
    }
    
    async checkAuthStatus() {
        try {
            const response = await fetch('/api/user_status');
            const data = response.json();
            
            if (data.logged_in) {
                this.currentUser = { id: data.user_id, username: data.username };
                this.phase = data.phase || null;
                this.showChatInterface(data);
                // If user is in questioning phase, start intake from frontend
                if (this.phase === 'questioning') {
                    this.startIntake();
                }
            } else {
                // If we have a saved session, show chat interface with recovered data
                if (this.messages.length > 0 || this.phase) {
                    this.showChatInterface(data);
                    // Re-enable input if in advice phase (not paywall yet)
                    if (this.phase === 'advice') {
                        this.setInputEnabled(true);
                    }
                } else {
                    // Fresh guest: enable input to allow starting intake
                    this.setInputEnabled(true);
                }
            }
        } catch (error) {
            console.error('Auth check failed:', error);
        }
    }
    
    async handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.currentUser = {id: data.user_id, username};
                this.showChatInterface(data);
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Connection error. Please try again.');
        }
    }
    
    async handleRegister(e) {
        e.preventDefault();
        const username = document.getElementById('registerUsername').value;
        const password = document.getElementById('registerPassword').value;
        
        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert('Account created! Please log in.');
                this.switchTab('login');
                this.loginForm.reset();
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Registration failed. Please try again.');
        }
    }
    
    showChatInterface(userData) {
        this.authModal.classList.remove('active');
        this.chatContainer.classList.remove('hidden');
        
        this.usernameDisplay.textContent = this.currentUser ? this.currentUser.username : 'Guest';
        this.setInputEnabled(true);
        this.isLoggedIn = true;
        
        this.scrollToBottom();
    }
    
    setInputEnabled(enabled) {
        this.messageInput.disabled = !enabled;
        this.sendBtn.disabled = !enabled;
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        // If phase not set yet (guest fresh), start intake first
        if (!this.phase) {
            await this.startIntake();
            return;
        }

        // Add user message to UI
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.setInputStatus('', '');
        this.sendBtn.disabled = true; 
        this.sendBtn.style.opacity = '0.6';

        try {
            // If currently in questioning/intake phase, submit answer endpoint
            if (this.phase === 'questioning') {
                const resp = await fetch('/api/submit_answer', {
                    method: 'POST', 
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({answer: message})
                });
                const data = await resp.json();
                if (resp.ok) {
                    if (data.done) {
                        // show final advice returned
                        if (data.advice) this.addMessage(data.advice, 'ai');
                        this.phase = 'advice';
                        this.saveSession();
                    } else {
                        // show next question to user
                        const nextQ = data.next_question || data.question;
                        if (nextQ) this.addMessage(nextQ, 'ai');
                    }
                } else {
                    this.addMessage(data.error || 'Problem with intake.', 'ai');
                }
            } else if (this.phase === 'paywall') {
                // Block all messages when paywall is active
                this.addMessage(this.t('paywall'), 'ai');
                this.setInputEnabled(false);
            } else {
                // Advice/chat mode
                // include guestId if not logged in
                const payload = this.currentUser ? {message} : {message, guest_id: this.guestId};
                // typing
                this.setInputStatus(this.t('typing'), 'typing');
                const resp = await fetch('/api/chat', {
                    method: 'POST', 
                    headers: {'Content-Type': 'application/json'}, 
                    body: JSON.stringify(payload)
                });
                const data = await resp.json();
                
                // Check for paywall response (402 status or paywall flag)
                if (resp.status === 402 || data.paywall) {
                    this.phase = 'paywall';
                    this.hasPaywallTriggered = true;
                    this.saveSession();
                    this.addMessage(data.message, 'ai');
                    this.setInputEnabled(false);
                    this.setInputStatus('', '');
                } else if (resp.ok) {
                    this.addMessage(data.response, 'ai');
                    this.setInputStatus('', '');
                } else {
                    this.addMessage(data.error || 'Sorry, something went wrong.', 'ai');
                    this.setInputStatus('', '');
                }
            }
            
            this.saveSession();
        } catch (err) {
            this.addMessage('Network error. Please try again.', 'ai');
            this.setInputStatus('', '');
        } finally {
            this.sendBtn.disabled = false; 
            this.sendBtn.style.opacity = '1';
        }
    }

    // Start intake from frontend (guest or logged-in)
    async startIntake() {
        try {
            const resp = await fetch('/api/start_intake', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({language: this.language})
            });
            const data = await resp.json();
            if (resp.ok) {
                this.phase = 'questioning';
                this.intakeIndex = 0;
                this.intakeAnswers = [];
                this.addMessage(data.privacy, 'ai');
                if (data.first_question) this.addMessage(data.first_question, 'ai');
                this.setInputEnabled(true);
                this.saveSession();
            }
        } catch (e) {
            console.error(e);
        }
    }

    ensureGuestId() {
        let id = localStorage.getItem('soul_companion_guest');
        if (!id) {
            id = 'guest_' + Math.random().toString(36).slice(2, 10);
            localStorage.setItem('soul_companion_guest', id);
        }
        return id;
    }
    
    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.innerHTML = `
            <div class="message-content">${this.formatMessage(text)}</div>
            <div class="message-time">${time}</div>
        `;
        
        this.messagesContainer.appendChild(messageDiv);
        
        // Store in memory
        this.messages.push({
            text: text,
            sender: sender,
            time: time
        });
        
        this.scrollToBottom();
    }
    
    formatMessage(text) {
        return text.replace(/\n/g, '<br>');
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    setInputStatus(message, type = '') {
        this.inputStatus.textContent = message;
        this.inputStatus.className = `input-status ${type}`;
    }
    
    showError(message) {
        alert(message);
    }
    
    logout() {
        fetch('/api/logout');
        this.resetInterface();
    }
    
    showUpgrade() {
        const msgPart1 = this.language === 'ar' ? 'هل تريد الترقية إلى Premium؟\n$9.99/شهر' :
                         this.language === 'fr' ? 'Voulez-vous passer à Premium?\n$9.99/mois' :
                         'Upgrade to Premium for unlimited sessions?\n$9.99/month';
        
        if (confirm(msgPart1 + '\n\nContinue?')) {
            const alertMsg = this.language === 'ar' ? 'قريباً! في الوقت الحالي، أنشئ حساباً جديداً للحصول على جلسة إضافية مجانية.' :
                            this.language === 'fr' ? 'Bientôt! Pour l\'instant, créez un nouveau compte pour une session gratuite supplémentaire.' :
                            'Premium upgrade coming soon! For now, create a new account for another free session.';
            alert(alertMsg);
        }
    }
    
    resetInterface() {
        this.authModal.classList.add('active');
        this.chatContainer.classList.add('hidden');
        this.messagesContainer.innerHTML = '';
        this.messages = [];
        this.currentUser = null;
        this.isLoggedIn = false;
        this.phase = null;
        this.intakeAnswers = [];
        this.intakeIndex = 0;
        this.hasPaywallTriggered = false;
        localStorage.removeItem('soul_companion_session');
        this.loginForm.reset();
        this.registerForm.reset();
        this.switchTab('login');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SoulCompanion();
});