document.addEventListener('DOMContentLoaded', function () {
    fetch('contas/api/addresses/')
        .then(response => response.json())
        .then(data => {
            const addressesDatalist = document.getElementById('addresses');
            addressesDatalist.innerHTML = '';
            data.forEach(address => {
                const option = document.createElement('option');
                option.value = address.complete_address;
                option.setAttribute('data-address-id', address.id);
                addressesDatalist.appendChild(option);
            });
        })
        .catch(error => console.error('Erro ao buscar endereços:', error));

    const addressInput = document.getElementById('address-input');
    const addressIdInput = document.getElementById('id_address');

    addressInput.addEventListener('input', function () {
        const inputValue = addressInput.value;
        const options = document.querySelectorAll('#addresses option');

        options.forEach(option => {
            if (option.value === inputValue) {
                addressIdInput.value = option.getAttribute('data-address-id');
                console.log('Endereço selecionado:', option.value);
                console.log('ID do endereço:', addressIdInput.value);
            }
        });
    });

    addressInput.addEventListener('change', function () {
        const inputValue = addressInput.value;
        const options = document.querySelectorAll('#addresses option');
        let isValid = false;

        options.forEach(option => {
            if (option.value === inputValue) {
                addressIdInput.value = option.getAttribute('data-address-id');
                isValid = true;
            }
        });

        if (!isValid) {
            addressIdInput.value = '';
        }
    });
});


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
    fetch('{% url "accounts:addresses_api" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
        .then(response => response.json())
        .then(data => {
            console.log('Sucesso:', data);

            // Cria um novo option com o endereço retornado e adiciona o novo option ao select de endereços
            var newOption = new Option(data.address_text, data.address_id, false, true);
            var selectElement = $('#id_address');
            selectElement.append(newOption).trigger('change');

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

$(document).ready(function () {
    $('#id_is_paid_now_yes').change(function () {
        $('#id_payment_method').prop('disabled', false);
    });
    $('#id_is_paid_now_no').change(function () {
        $('#id_payment_method').prop('disabled', true);
    });

    if ($('#id_is_paid_now_no').is(':checked')) {
        $('#id_payment_method').hide();
    }

    $('#id_is_paid_now_no').click(function () {
        $('#id_payment_method').hide();
    });

    $('#id_is_paid_now_yes').click(function () {
        $('#id_payment_method').show();
    });

    $('#id_customer_wants_invoice').change(function () {
        if ($(this).is(':checked') && $('#id_price').val() != '') {
            var price = parseFloat($('#id_price').val());
            var confirmAdd = confirm('Deseja acrescentar R$ 30,00 ao preço?');
            if (confirmAdd) {
                price += 30;
                $('#id_price').val(price.toFixed(2));
            }
        }
        if (!$(this).is(':checked') && $('#id_price').val() != '') {
            var price = parseFloat($('#id_price').val());
            var confirmAdd = confirm('Deseja subtrair R$ 30,00 ao preço?');
            if (confirmAdd) {
                price -= 30;
                $('#id_price').val(price.toFixed(2));
            }
        }
    });
});