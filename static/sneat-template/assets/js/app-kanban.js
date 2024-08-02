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
        comments: task.comments || "0",
        'badge-text': task.badgeText || "",
        badge: task.badge || "default",
        'due-date': task.dueDate || "",
        attachments: task.attachments || "0",
        assigned: task.assigned || [],
        members: task.members || []
      }))
    }));
  }

  // Fazer a requisição para obter os dados do kanban
  fetch('/quadros/api/1/')
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

  function renderFooter(attachments, comments, assigned, members) {
    return (
      "<div class='d-flex justify-content-between align-items-center flex-wrap mt-2 pt-1'>" +
      "<div class='d-flex'> <span class='d-flex align-items-center me-2'><i class='bx bx-paperclip me-1'></i>" +
      "<span class='attachments'>" +
      attachments +
      '</span>' +
      "</span> <span class='d-flex align-items-center ms-2'><i class='bx bx-chat me-1'></i>" +
      '<span> ' +
      comments +
      ' </span>' +
      '</span></div>' +
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
        // Prevent any actions on click
        return;
      }
    });

    // Render custom items
    const kanbanItem = [].slice.call(document.querySelectorAll('.kanban-item'));
    if (kanbanItem) {
      kanbanItem.forEach(function (el) {
        const title = el.querySelector('.kanban-text').innerText;
        const element = "<span class='kanban-text'>" + title + '</span>';
        let img = '';
        if (el.getAttribute('data-image') !== null) {
          img = "<img class='img-fluid rounded-3 mb-2' src='" + assetsPath + 'img/elements/' + el.getAttribute('data-image') + "'>";
        }
        el.textContent = '';
        el.insertAdjacentHTML('beforeend', element);
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

  // Kanban Wrapper scrollbar
  if (kanbanWrapper) {
    new PerfectScrollbar(kanbanWrapper);
  }
})();
