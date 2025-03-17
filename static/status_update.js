// Constantes para os status
const STATUS_TYPES = {
    1: "Em Formação",
    2: "Em Transporte",
    3: "Em Plantio",
    4: "Plantado"
};

let currentPlantioCode = null;

// Variáveis para armazenar as coordenadas
let latitude = null;
let longitude = null;

// Função para obter a localização atual
function obterLocalizacao() {
    return new Promise((resolve, reject) => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    latitude = position.coords.latitude;
                    longitude = position.coords.longitude;
                    resolve({ latitude, longitude });
                },
                (error) => {
                    console.error("Erro ao obter localização:", error);
                    reject(error);
                }
            );
        } else {
            const error = "Geolocalização não é suportada por este navegador.";
            console.error(error);
            reject(error);
        }
    });
}

// Função para abrir o modal de status
function abrirModalStatus(codigo) {
    currentPlantioCode = codigo;
    const statusModal = new bootstrap.Modal(document.getElementById('statusModal'));
    statusModal.show();
}

// Função para atualizar o status
function atualizarStatus(event) {
    event.preventDefault();
    
    // Verificar se o usuário quer capturar a localização
    const capturarLocalizacao = document.getElementById('capturarLocalizacao').checked;
    
    // Mostrar indicador de carregamento
    document.getElementById('statusSubmitBtn').disabled = true;
    document.getElementById('statusSubmitBtn').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Atualizando...';
    
    // Função para enviar os dados
    const enviarDados = (coords = null) => {
        const formData = {
            codigo: currentPlantioCode,
            status: document.getElementById('statusSelect').value,
            observacao: document.getElementById('statusObservacao').value,
            usuario: document.getElementById('statusUsuario').value || document.getElementById('statusUsuario').getAttribute('data-usuario-logado')
        };
        
        // Adicionar coordenadas se disponíveis
        if (coords) {
            formData.latitude = coords.latitude;
            formData.longitude = coords.longitude;
        }
        
        // Enviar para o servidor
        fetch('/atualizar-status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            // Restaurar botão
            document.getElementById('statusSubmitBtn').disabled = false;
            document.getElementById('statusSubmitBtn').innerHTML = '<i class="fas fa-save me-2"></i>Atualizar';
            
            if (data.success) {
                // Fechar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('statusModal'));
                modal.hide();
                
                // Mostrar mensagem de sucesso
                mostrarAlerta('success', 'Status atualizado com sucesso!');
                
                // Recarregar histórico de status
                carregarHistoricoStatus(currentPlantioCode);
            } else {
                mostrarAlerta('danger', data.message || 'Erro ao atualizar status.');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            document.getElementById('statusSubmitBtn').disabled = false;
            document.getElementById('statusSubmitBtn').innerHTML = '<i class="fas fa-save me-2"></i>Atualizar';
            mostrarAlerta('danger', 'Erro ao atualizar status. Por favor, tente novamente.');
        });
    };
    
    // Se o usuário quer capturar a localização, obter coordenadas
    if (capturarLocalizacao) {
        obterLocalizacao()
            .then(coords => {
                enviarDados(coords);
            })
            .catch(error => {
                console.error("Erro ao obter localização:", error);
                mostrarAlerta('warning', 'Não foi possível obter sua localização. O status será atualizado sem coordenadas.');
                enviarDados();
            });
    } else {
        // Enviar sem coordenadas
        enviarDados();
    }
}

// Função para carregar o histórico de status
function carregarHistoricoStatus(codigo) {
    fetch(`/historico-status/${codigo}`)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('statusHistoricoContainer');
            
            if (!data.historico || data.historico.length === 0) {
                container.innerHTML = '<p class="text-center text-muted">Nenhum histórico de status disponível.</p>';
                return;
            }
            
            let html = '<div class="status-timeline">';
            
            data.historico.forEach((status, index) => {
                const statusClass = index === 0 ? 'status-item current' : 'status-item';
                
                html += `
                    <div class="${statusClass}">
                        <div class="status-header">
                            <span class="status-badge badge bg-${getStatusColor(status.status)}">${status.status_texto}</span>
                            <span class="status-date"><i class="far fa-clock me-1"></i>${status.data_hora}</span>
                        </div>
                        <div class="status-body">
                            <p><strong><i class="fas fa-user me-1"></i> Usuário:</strong> ${status.usuario}</p>
                            <p><strong><i class="fas fa-comment me-1"></i> Observação:</strong> ${status.observacao}</p>
                            ${status.localizacao ? `
                            <p>
                                <strong><i class="fas fa-map-marker-alt me-1"></i> Localização:</strong> 
                                <a href="https://maps.google.com/?q=${status.localizacao.latitude},${status.localizacao.longitude}" target="_blank">
                                    ${status.localizacao.latitude.toFixed(6)}, ${status.localizacao.longitude.toFixed(6)}
                                    <i class="fas fa-external-link-alt ms-1 small"></i>
                                </a>
                            </p>` : ''}
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            container.innerHTML = html;
        })
        .catch(error => {
            console.error('Erro ao carregar histórico:', error);
        });
}

// Função para obter a cor do status
function getStatusColor(status) {
    switch (parseInt(status)) {
        case 0: return 'secondary'; // Em Formação
        case 1: return 'info';      // Em Transporte
        case 2: return 'warning';   // Em Plantio
        case 3: return 'success';   // Plantado
        default: return 'secondary';
    }
}

// Função para mostrar alertas
function mostrarAlerta(tipo, mensagem) {
    const alertPlaceholder = document.getElementById('alertPlaceholder');
    const wrapper = document.createElement('div');
    wrapper.innerHTML = `
        <div class="alert alert-${tipo} alert-dismissible fade show" role="alert">
            ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    alertPlaceholder.appendChild(wrapper);
    
    // Remover alerta após 5 segundos
    setTimeout(() => {
        const alert = wrapper.querySelector('.alert');
        if (alert) {
            bootstrap.Alert.getOrCreateInstance(alert).close();
        }
    }, 5000);
}
