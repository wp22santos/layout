// Gerenciador do Calendário
class CalendarManager {
    constructor() {
        this.calendarInstance = null;
        this.selectedDates = [];
        this.monthNames = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ];
    }

    initialize(containerId) {
        // Configuração do calendário
        const config = {
            locale: 'pt',
            dateFormat: 'd/m/Y',
            disableMobile: true,
            inline: true,
            onChange: this.handleDateChange.bind(this)
        };

        this.calendarInstance = flatpickr(containerId, config);
        
        // Inicializar pickers de data e hora
        this.initializeDatePickers();
        this.initializeTimePickers();
    }

    initializeDatePickers() {
        // Configuração para campos de data simples
        const datePickers = document.querySelectorAll('input[name="data"]');
        datePickers.forEach(picker => {
            flatpickr(picker, {
                locale: 'pt',
                dateFormat: 'd/m/Y',
                disableMobile: true
            });
        });
    }

    initializeTimePickers() {
        // Configuração para campos de hora
        const timePickers = document.querySelectorAll('.time-picker');
        timePickers.forEach(picker => {
            flatpickr(picker, {
                locale: 'pt',
                enableTime: true,
                noCalendar: true,
                dateFormat: 'H:i',
                time_24hr: true,
                disableMobile: true
            });
        });
    }

    handleDateChange(selectedDates) {
        this.selectedDates = selectedDates;
        const dataInput = document.getElementById('data-nao-contabil');
        if (dataInput && selectedDates.length > 0) {
            const formattedDate = selectedDates[0].toLocaleDateString('pt-BR');
            dataInput.value = formattedDate;
        }
    }
}

// Gerenciador do Modal
class ModalManager {
    constructor(modalId) {
        this.modal = document.getElementById(modalId);
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Fechar modal quando clicar fora
        window.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.hide();
            }
        });

        // Fechar modal com tecla ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.modal.classList.contains('hidden')) {
                this.hide();
            }
        });
    }

    show() {
        this.modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    hide() {
        this.modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

// Gerenciador de Tabs
class TabManager {
    constructor() {
        this.tabs = {
            turnos: {
                tab: document.getElementById('tab-turnos'),
                content: document.getElementById('content-turnos')
            },
            naoContabeis: {
                tab: document.getElementById('tab-nao-contabeis'),
                content: document.getElementById('content-nao-contabeis')
            }
        };
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Adicionar listeners para as tabs
        Object.keys(this.tabs).forEach(tabName => {
            const tab = this.tabs[tabName].tab;
            if (tab) {
                tab.addEventListener('click', () => this.switchTab(tabName));
            }
        });
    }

    switchTab(tabName) {
        // Atualizar estilos das tabs
        Object.keys(this.tabs).forEach(name => {
            const tab = this.tabs[name].tab;
            const content = this.tabs[name].content;
            
            if (name === tabName) {
                tab.classList.remove('bg-gray-100', 'text-gray-600');
                tab.classList.add('btn-primary');
                content.classList.remove('hidden');
            } else {
                tab.classList.add('bg-gray-100', 'text-gray-600');
                tab.classList.remove('btn-primary');
                content.classList.add('hidden');
            }
        });
    }
}

// Setup dos formulários
function setupFormHandlers() {
    const formTurnos = document.getElementById('form-turnos');
    const formNaoContabeis = document.getElementById('form-nao-contabeis');

    if (formTurnos) {
        formTurnos.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const response = await fetch(formTurnos.action, {
                    method: 'POST',
                    body: new FormData(formTurnos)
                });
                
                const result = await response.json();
                if (result.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Sucesso!',
                        text: 'Turno registrado com sucesso!'
                    }).then(() => {
                        window.location.reload();
                    });
                } else {
                    throw new Error(result.message || 'Erro ao registrar turno');
                }
            } catch (error) {
                Swal.fire({
                    icon: 'error',
                    title: 'Erro!',
                    text: error.message || 'Erro ao processar sua solicitação'
                });
            }
        });
    }

    if (formNaoContabeis) {
        formNaoContabeis.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const response = await fetch(formNaoContabeis.action, {
                    method: 'POST',
                    body: new FormData(formNaoContabeis)
                });
                
                const result = await response.json();
                if (result.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Sucesso!',
                        text: 'Dia não contábil registrado com sucesso!'
                    }).then(() => {
                        window.location.reload();
                    });
                } else {
                    throw new Error(result.message || 'Erro ao registrar dia não contábil');
                }
            } catch (error) {
                Swal.fire({
                    icon: 'error',
                    title: 'Erro!',
                    text: error.message || 'Erro ao processar sua solicitação'
                });
            }
        });
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar gerenciadores
    const calendarManager = new CalendarManager();
    const modalManager = new ModalManager('modalLancamentos');
    const tabManager = new TabManager();

    // Inicializar calendário
    calendarManager.initialize('#calendario');

    // Configurar handlers para formulários
    setupFormHandlers();

    // Expor modalManager globalmente para o botão de lançamento
    window.modalManager = modalManager;
});
