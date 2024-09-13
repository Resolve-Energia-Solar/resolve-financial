'use strict';

(async function () {
  let boards;
  const kanbanWrapper = document.querySelector('.kanban-wrapper'),
    assetsPath = document.querySelector('html').getAttribute('data-assets-path');

  // Função para transformar os dados recebidos no formato desejado
  function transformKanbanData(data) {
    return data.columns.map(column => ({
      id: `column-${column.id}`,
      title: column.title,
      item: column.tasks.map(task => ({
        id: `task-${task.id}`,
        title: task.title,
        description: task.description || "", // Adicionando a descrição do lead
        comments: task.comments || "0", // Caso existam comentários
        'badge-text': task.badgeText || "", // Adiciona o texto do badge, se existir
        badge: task.badge || "default", // Adiciona o badge, se existir
        'due-date': task.due_date || "", // Data de vencimento (data de nascimento ou outra)
        attachments: task.attachments || "0", // Caso existam anexos
        assigned: task.owner, // Dono do lead (vendedor)
        members: task.members || [], // Lista de membros, se aplicável
        email: task.email || "", // E-mail do lead
        phone: task.phone || "", // Telefone do lead
        url: task.url || "", // URL para detalhes do lead
        created_at: task.created_at || "", // Data de criação
      }))
    }));
  }


  // Fazer a requisição para obter os dados do kanban
  fetch('/crm/leads/kanban/api/1/')
    .then(response => response.json())
    .then(data => {
      const transformedData = transformKanbanData(data);
      boards = transformedData;
      initKanban();
    })
    .catch(error => {
      console.error('Erro ao buscar os dados do kanban:', error);
    });

  function renderAvatar(images, pullUp, size, margin, members) {
    var $transition = pullUp ? ' pull-up' : '',
      $size = size ? 'avatar-' + size + '' : '',
      member = members == undefined ? ' ' : members.split(',');

    return images == undefined
      ? ' '
      : images
        .split(',')
        .map(function (img, index, arr) {
          var $margin = margin && index !== arr.length - 1 ? ' me-' + margin + '' : '';
          return (
            "<div class='avatar " +
            $size +
            $margin +
            "'" +
            "data-bs-toggle='tooltip' data-bs-placement='top'" +
            "title='" +
            member[index] +
            "'" +
            '>' +
            "<img src='" +
            assetsPath +
            'img/avatars/' +
            img +
            "' alt='Avatar' class='rounded-circle " +
            $transition +
            "'>" +
            '</div>'
          );
        })
        .join(' ');
  }

  function renderFooter(attachments, comments, assigned, members, email, phone) {
    return (
      "<div class='d-flex justify-content-between align-items-center flex-wrap mt-2 pt-1'>" +
      "<div class='d-flex'> " +
      "<span class='d-flex align-items-center me-2'><i class='bx bx-envelope me-1'></i>" +
      "<span class='email'>" + email + "</span>" +
      "</span> " +
      "<span class='d-flex align-items-center ms-2'><i class='bx bx-phone me-1'></i>" +
      "<span class='phone'> " + phone + " </span>" +
      "</span> </div>" +
      "<div class='avatar-group d-flex align-items-center assigned-avatar'>" +
      renderAvatar(assigned, true, 'xs', null, members) +
      '</div>' +
      '</div>'
    );
  }

  // Init kanban
  function initKanban() {
    const kanban = new jKanban({
      element: '.kanban-wrapper',
      gutter: '15px',
      widthBoard: '250px',
      boards: boards,
      dragBoards: false, // Disable dragging of boards
      dragItems: false, // Disable dragging of items
      addItemButton: false, // Disable adding new items
      click: function (el) {
        const itemId = el.dataset.eid;
        const board = boards.find(board => board.item.some(item => item.id === itemId));
        const item = board ? board.item.find(item => item.id === itemId) : null;
        if (item) {
          showModal(item);
        } else {
          console.error('Item não encontrado:', itemId);
        }
      }
    });

    // Render custom items
    const kanbanItem = [].slice.call(document.querySelectorAll('.kanban-item'));
    if (kanbanItem) {
      kanbanItem.forEach(function (el) {
        // Extrair o texto diretamente do elemento .kanban-item
        const title = el.textContent.trim(); // Pega o texto diretamente do elemento

        // Cria um novo elemento com a classe .kanban-text para armazenar o título
        const element = "<span class='kanban-text'>" + title + '</span>';

        let img = '';
        if (el.getAttribute('data-image') !== null) {
          img = "<img class='img-fluid rounded-3 mb-2' src='" + assetsPath + 'img/elements/' + el.getAttribute('data-image') + "'>";
        }

        el.textContent = ''; // Limpa o conteúdo existente antes de adicionar o novo
        el.insertAdjacentHTML('beforeend', element); // Insere o título dentro de .kanban-text
        el.insertAdjacentHTML('beforeend', img); // Adiciona a imagem, se existir

        // Adiciona o rodapé (comentários, data, anexos, etc.)
        if (
          el.getAttribute('data-comments') !== undefined ||
          el.getAttribute('data-due-date') !== undefined ||
          el.getAttribute('data-assigned') !== undefined
        ) {
          el.insertAdjacentHTML(
            'beforeend',
            renderFooter(
              el.getAttribute('data-attachments'),
              el.getAttribute('data-comments'),
              el.getAttribute('data-assigned'),
              el.getAttribute('data-members')
            )
          );
        }
      });
    }

    // To initialize tooltips for rendered items
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }

  function showModal(item) {
    const modal = new bootstrap.Modal(document.getElementById('taskModal'));
    document.getElementById('task-title').innerText = item.title;
    document.getElementById('task-comments').innerText = item.description;
    document.getElementById('task-badge').innerText = item.status;
    document.getElementById('task-due-date').innerText = item['due-date'];
    document.getElementById('task-attachments').innerText = item.attachments;
    document.getElementById('task-assigned').innerText = item.assigned;
    document.getElementById('task-created-at').innerText = item.created_at;
    modal.show();
  }

  // Kanban Wrapper scrollbar
  if (kanbanWrapper) {
    new PerfectScrollbar(kanbanWrapper);
  }
})();