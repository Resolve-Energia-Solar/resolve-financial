document.getElementById('createAddressForm').addEventListener('submit', function (e) {
    e.preventDefault(); // Impede o envio padrão do formulário

    // Coleta os dados do formulário
    var formData = {
        street: document.getElementById('id_street').value,
        city: document.getElementById('id_city').value,
        state: document.getElementById('id_state').value,
        zip_code: document.getElementById('id_zip_code').value,
        country: document.getElementById('id_country').value,
        neighborhood: document.getElementById('id_neighborhood').value,
        number: document.getElementById('id_number').value,
        complement: document.getElementById('id_complement').value
    };

    // Envia os dados para a API
    fetch('/conta/api/addresses/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
        .then(response => response.json())
        .then(data => {
            console.log('Sucesso:', data);

            // Fecha o modal
            var modalElement = document.getElementById('createAddressModal');
            var modalInstance = bootstrap.Modal.getInstance(modalElement);
            modalInstance.hide();
        })
        .catch((error) => {
            console.error('Erro:', error);
        });
});


document.getElementById('id_zip_code').addEventListener('blur', function () {
    const cep = this.value.replace(/\D/g, ''); // Remove caracteres não numéricos
    const fieldsToDisable = ['id_zip_code', 'id_street', 'id_neighborhood', 'id_city', 'id_state', 'id_complement', 'id_country'];
    const submitButton = document.querySelector('.modal button[type="submit"]');
    const originalButtonContent = submitButton.innerHTML; // Armazena o conteúdo original do botão

    // Função para alterar o botão para o indicador de carregamento
    function setLoadingIndicator(isLoading) {
        if (isLoading) {
            submitButton.innerHTML = '<span class="spinner-grow spinner-grow-sm text-secondary me-1" aria-hidden="true"></span> Aguarde...';
            submitButton.disabled = true; // Desativa o botão para evitar múltiplos cliques
        } else {
            submitButton.innerHTML = originalButtonContent; // Restaura o conteúdo original do botão
            submitButton.disabled = false; // Reativa o botão
        }
    }

    function toggleFields(isLoading) {
        fieldsToDisable.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.disabled = isLoading;
            }
        });
        setLoadingIndicator(isLoading);
    }

    if (cep.length === 8) {
        toggleFields(true); // Desabilita os campos enquanto busca o CEP
        fetch(`https://brasilapi.com.br/api/cep/v1/${cep}`)
            .then(response => response.json())
            .then(data => {
                if (data.type && data.type === "service_error") {
                    // Trata o erro de serviço
                    console.error('Erro ao buscar o CEP:', data);
                    let errorMessage = 'Todos os serviços de CEP retornaram erro. Por favor, verifique o CEP ou tente novamente mais tarde.';
                    alert(errorMessage);
                } else {
                    document.getElementById('id_street').value = data.street;
                    document.getElementById('id_neighborhood').value = data.neighborhood;
                    document.getElementById('id_city').value = data.city;
                    document.getElementById('id_state').value = data.state;
                    document.getElementById('id_country').value = "Brasil";
                }
            })
            .catch(error => console.error('Erro ao buscar o CEP no segundo serviço:', error))
            .finally(() => {
                toggleFields(false);
            });
    } else {
        alert("CEP inválido. O CEP deve conter 8 dígitos.");
    }
});