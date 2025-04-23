document.addEventListener('DOMContentLoaded', async () => {
    const input = document.getElementById('id_financial_instituition');
    const parent = input.parentNode;

    const select = document.createElement('select');
    select.name = input.name;
    select.id = input.id;
    select.className = input.className;

    try {
        const res = await fetch('https://brasilapi.com.br/api/banks/v1');
        const data = await res.json();

        data
            .filter(bank => bank.code !== null)
            .sort((a, b) => a.code - b.code)
            .forEach(bank => {
                const option = document.createElement('option');
                option.value = `${bank.code} - ${bank.name}`;
                option.textContent = `${bank.code} - ${bank.fullName}`;
                select.appendChild(option);
            });

        parent.replaceChild(select, input);
    } catch (e) {
        console.error('Erro ao carregar bancos:', e);
    }
});