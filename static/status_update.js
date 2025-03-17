// Constantes para os status
const STATUS_TYPES = {
    1: "Em Formação",
    2: "Em Transporte",
    3: "Em Plantio",
    4: "Plantado"
};

let currentPlantioCode = null;

// Função para abrir o modal de status
function abrirModalStatus(codigo) {
    currentPlantioCode = codigo;
    const statusModal = new bootstrap.Modal(document.getElementById('statusModal'));
    statusModal.show();
}

// Função para atualizar o status
function atualizarStatus(event) {
    event.preventDefault();
    
    const formData = {
        codigo: currentPlantioCode,
        status: document.getElementById('statusSelect').value,
        observacao: document.getElementById('statusObservacao').value,
        usuario: document.getElementById('statusUsuario').value || document.getElementById('statusUsuario').getAttribute('data-usuario-logado')
    };

    // Mostrar indicador de carregamento
    document.getElementById('statusSubmitBtn').disabled = true;
    document.getElementById('statusSubmitBtn').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Atualizando...';

    fetch('/atualizar-status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Fechar o modal
            const statusModal = bootstrap.Modal.getInstance(document.getElementById('statusModal'));
            statusModal.hide();
            
            // Mostrar mensagem de sucesso
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-success alert-dismissible fade show';
            alertDiv.innerHTML = `
                <i class="fas fa-check-circle me-2"></i>Status atualizado com sucesso!
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            document.getElementById('alertContainer').appendChild(alertDiv);
            
            // Atualizar o histórico
            carregarHistoricoStatus(currentPlantioCode);
            
            // Limpar o formulário
            document.getElementById('statusForm').reset();
        } else {
            alert('Erro ao atualizar status: ' + data.message);
        }
        
        // Restaurar o botão
        document.getElementById('statusSubmitBtn').disabled = false;
        document.getElementById('statusSubmitBtn').innerHTML = '<i class="fas fa-save me-2"></i>Atualizar';
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro ao atualizar status');
        
        // Restaurar o botão
        document.getElementById('statusSubmitBtn').disabled = false;
        document.getElementById('statusSubmitBtn').innerHTML = '<i class="fas fa-save me-2"></i>Atualizar';
    });
}

// Função para carregar o histórico de status
function carregarHistoricoStatus(codigo) {
    fetch(`/historico-status/${codigo}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const historicoContainer = document.getElementById('historicoStatus');
                
                if (data.historico && data.historico.length > 0) {
                    // Ordenar por data (mais recente primeiro)
                    const historico = data.historico.sort((a, b) => {
                        return new Date(b.data_hora) - new Date(a.data_hora);
                    });
                    
                    const historicoHtml = historico
                        .map(status => `
                            <div class="status-item">
                                <div class="status-header">
                                    <span class="badge status-${status.status}">${status.status_texto}</span>
                                    <small class="text-muted">${status.data_hora}</small>
                                </div>
                                <div class="status-body">
                                    <p><strong><i class="fas fa-user me-1"></i> Usuário:</strong> ${status.usuario}</p>
                                    <p><strong><i class="fas fa-comment me-1"></i> Observação:</strong> ${status.observacao}</p>
                                </div>
                            </div>
                        `)
                        .join('');
                    
                    historicoContainer.innerHTML = historicoHtml;
                    
                    // Atualizar o status atual
                    if (historico.length > 0) {
                        const statusAtual = historico[0];
                        document.getElementById('statusAtualBadge').className = `badge status-${statusAtual.status}`;
                        document.getElementById('statusAtualBadge').textContent = statusAtual.status_texto;
                    }
                } else {
                    historicoContainer.innerHTML = `
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i>Nenhum histórico de status disponível.
                        </div>
                    `;
                }
            }
        })
        .catch(error => {
            console.error('Erro ao carregar histórico:', error);
        });
}
