/**
 * App Kanban
 */

'use strict';

document.addEventListener('DOMContentLoaded', function () {
  const boardId = document.querySelector('.app-kanban').getAttribute('data-board-id');
  const apiUrl = `/quadros/api/${boardId}/`;

  // Função para transformar os dados recebidos no formato desejado
  function transformKanbanData(data) {
    return data.columns.map(column => ({
      id: `column-${column.id}`,
      title: column.title,
      item: [
        {
          "id": "in-progress-1",
          "title": "Exemplo",
          "comments": "3",
          "badge-text": "Exemplo",
          "badge": "success",
          "attachments": "1",
          "assigned": [
            "12.png",
            "5.png"
          ],
          "members": [
            "Beatriz Costa",
            "Kevin Kley"
          ]
        },
        {
          "id": "in-progress-1",
          "title": "Segundo Exemplo",
          "comments": "5",
          "badge-text": "Exemplo",
          "badge": "success",
          "attachments": "3",
          "assigned": [
            "12.png",
            "5.png"
          ],
          "members": [
            "Larissa Paiva",
            "Leonardo Costa"
          ]
        }]
    }));
  }
  // Função para inicializar o Kanban com os dados das colunas
  function initializeKanban(columns) {
    new jKanban({
      element: '.kanban-wrapper',
      gutter: '12px',
      widthBoard: '250px',
      boards: columns,
      dragBoards: true,
      dragItems: false,
      addItemButton: false,
    });
  }

  // Função para buscar os dados da API e inicializar o Kanban
  function loadKanbanBoard() {
    fetch(apiUrl)
      .then(response => response.json())
      .then(data => {
        const columns = transformKanbanData(data);
        initializeKanban(columns);
      })
      .catch(error => console.error('Erro ao carregar os dados do Kanban:', error));
  }

  const kanbanSidebar = document.querySelector('.kanban-update-item-sidebar'),
    kanbanWrapper = document.querySelector('.kanban-wrapper'),
    kanbanAddNewBoard = document.querySelector('.kanban-add-new-board'),
    kanbanAddNewInput = [].slice.call(document.querySelectorAll('.kanban-add-board-input')),
    kanbanAddBoardBtn = document.querySelector('.kanban-add-board-btn'),
    datePicker = document.querySelector('#due-date'),
    select2 = $('.select2'), // ! Using jquery vars due to select2 jQuery dependency
    assetsPath = document.querySelector('html').getAttribute('data-assets-path');


  // Fetch data from API
  boards = loadKanbanBoard()

  // datepicker init
  if (datePicker) {
    datePicker.flatpickr({
      monthSelectorType: 'static',
      altInput: true,
      altFormat: 'j F, Y',
      dateFormat: 'Y-m-d'
    });
  }

  //! TODO: Update Event label and guest code to JS once select removes jQuery dependency
  // select2
  if (select2.length) {
    function renderLabels(option) {
      if (!option.id) {
        return option.text;
      }
      var $badge = "<div class='badge " + $(option.element).data('color') + " rounded-pill'> " + option.text + '</div>';
      return $badge;
    }

    select2.each(function () {
      var $this = $(this);
      $this.wrap("<div class='position-relative'></div>").select2({
        placeholder: 'Select Label',
        dropdownParent: $this.parent(),
        templateResult: renderLabels,
        templateSelection: renderLabels,
        escapeMarkup: function (es) {
          return es;
        }
      });
    });
  }


  // Render board dropdown
  function renderBoardDropdown() {
    return (
      "<div class='dropdown'>" +
      "<i class='dropdown-toggle bx bx-dots-vertical-rounded cursor-pointer fs-4' id='board-dropdown' data-bs-toggle='dropdown' aria-haspopup='true' aria-expanded='false'></i>" +
      "<div class='dropdown-menu dropdown-menu-end' aria-labelledby='board-dropdown'>" +
      "<a class='dropdown-item delete-board' href='javascript:void(0)'> <i class='bx bx-trash bx-xs'></i> <span class='align-middle'>Delete</span></a>" +
      "<a class='dropdown-item' href='javascript:void(0)'><i class='bx bx-rename bx-xs'></i> <span class='align-middle'>Rename</span></a>" +
      "<a class='dropdown-item' href='javascript:void(0)'><i class='bx bx-archive bx-xs'></i> <span class='align-middle'>Archive</span></a>" +
      '</div>' +
      '</div>'
    );
  }
  // Render item dropdown
  function renderDropdown() {
    return (
      "<div class='dropdown kanban-tasks-item-dropdown'>" +
      "<i class='dropdown-toggle bx bx-dots-vertical-rounded' id='kanban-tasks-item-dropdown' data-bs-toggle='dropdown' aria-haspopup='true' aria-expanded='false'></i>" +
      "<div class='dropdown-menu dropdown-menu-end' aria-labelledby='kanban-tasks-item-dropdown'>" +
      "<a class='dropdown-item' href='javascript:void(0)'>Copy task link</a>" +
      "<a class='dropdown-item' href='javascript:void(0)'>Duplicate task</a>" +
      "<a class='dropdown-item delete-task' href='javascript:void(0)'>Delete</a>" +
      '</div>' +
      '</div>'
    );
  }
  // Render header
  function renderHeader(color, text) {
    return (
      "<div class='d-flex justify-content-between flex-wrap align-items-center mb-2 pb-1'>" +
      "<div class='item-badges'> " +
      "<div class='badge rounded-pill bg-label-" +
      color +
      "'> " +
      text +
      '</div>' +
      '</div>' +
      renderDropdown() +
      '</div>'
    );
  }

  // Render avatar
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

  // Render footer
  function renderFooter(attachments, comments, assigned, members) {
    return (
      "<div class='d-flex justify-content-between align-items-center flex-wrap mt-2 pt-1'>" +
      "<div class='d-flex'> <span class='d-flex align-items-center me-2'><i class='bx bx-paperclip me-1'></i>" +
      "<span class='attachments'>" +
      attachments +
      '</span>' +
      "</span> <span class='d-flex align-items-center'><i class='bx bx-chat me-1'></i>" +
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
  const kanban = new jKanban({
    element: '.kanban-wrapper',
    gutter: '15px',
    widthBoard: '250px',
    dragItems: true,
    boards: boards,
    dragBoards: true,
    addItemButton: true,
    buttonContent: '+ Add Item',
    click: function (el) {
      let element = el;
      let title = element.getAttribute('data-eid')
        ? element.querySelector('.kanban-text').textContent
        : element.textContent,
        date = element.getAttribute('data-due-date'),
        dateObj = new Date(),
        year = dateObj.getFullYear(),
        dateToUse = date
          ? date + ', ' + year
          : dateObj.getDate() + ' ' + dateObj.toLocaleString('en', { month: 'long' }) + ', ' + year,
        label = element.getAttribute('data-badge-text'),
        avatars = element.getAttribute('data-assigned');

      // To get data on sidebar
      kanbanSidebar.querySelector('#title').value = title;
      kanbanSidebar.querySelector('#due-date').nextSibling.value = dateToUse;

      // ! Using jQuery method to get sidebar due to select2 dependency
      $('.kanban-update-item-sidebar').find(select2).val(label).trigger('change');

      // Remove & Update assigned
      kanbanSidebar.querySelector('.assigned').innerHTML = '';
      kanbanSidebar
        .querySelector('.assigned')
        .insertAdjacentHTML(
          'afterbegin',
          renderAvatar(avatars, false, 'sm', '0', el.getAttribute('data-members')) +
          "<div class='avatar avatar-sm'>" +
          "<span class='avatar-initial rounded-circle bg-label-secondary'><i class='bx bx-plus'></i></span>" +
          '</div>'
        );
    },

    buttonClick: function (el, boardId) {
      const addNew = document.createElement('form');
      addNew.setAttribute('class', 'new-item-form');
      addNew.innerHTML =
        '<div class="mb-3">' +
        '<textarea class="form-control add-new-item" rows="2" placeholder="Adicionar conteúdo" autofocus required></textarea>' +
        '</div>' +
        '<div class="mb-3">' +
        '<button type="submit" class="btn btn-primary btn-sm me-2">Adicionar</button>' +
        '<button type="button" class="btn btn-label-secondary btn-sm cancel-add-item">Cancelar</button>' +
        '</div>';
      kanban.addForm(boardId, addNew);

      addNew.addEventListener('submit', function (e) {
        e.preventDefault();
        const currentBoard = [].slice.call(
          document.querySelectorAll('.kanban-board[data-id=' + boardId + '] .kanban-item')
        );
        kanban.addElement(boardId, {
          title: "<span class='kanban-text'>" + e.target[0].value + '</span>',
          id: boardId + '-' + currentBoard.length + 1
        });

        // add dropdown in new boards
        const kanbanText = [].slice.call(
          document.querySelectorAll('.kanban-board[data-id=' + boardId + '] .kanban-text')
        );
        kanbanText.forEach(function (e) {
          e.insertAdjacentHTML('beforebegin', renderDropdown());
        });

        // prevent sidebar to open onclick dropdown buttons of new tasks
        const newTaskDropdown = [].slice.call(document.querySelectorAll('.kanban-item .kanban-tasks-item-dropdown'));
        if (newTaskDropdown) {
          newTaskDropdown.forEach(function (e) {
            e.addEventListener('click', function (el) {
              el.stopPropagation();
            });
          });
        }

        // delete tasks for new boards
        const deleteTask = [].slice.call(
          document.querySelectorAll('.kanban-board[data-id=' + boardId + '] .delete-task')
        );
        deleteTask.forEach(function (e) {
          e.addEventListener('click', function () {
            const id = this.closest('.kanban-item').getAttribute('data-eid');
            kanban.removeElement(id);
          });
        });
        addNew.remove();
      });

      // Remove form on clicking cancel button
      addNew.querySelector('.cancel-add-item').addEventListener('click', function (e) {
        addNew.remove();
      });
    }
  });

  // Kanban Wrapper scrollbar
  if (kanbanWrapper) {
    new PerfectScrollbar(kanbanWrapper);
  }

  const kanbanContainer = document.querySelector('.kanban-container'),
    kanbanTitleBoard = [].slice.call(document.querySelectorAll('.kanban-title-board')),
    kanbanItem = [].slice.call(document.querySelectorAll('.kanban-item'));

  // Render custom items
  if (kanbanItem) {
    kanbanItem.forEach(function (el) {
      const element = "<span class='kanban-text'>" + el.textContent + '</span>';
      let img = '';
      if (el.getAttribute('data-image') !== null) {
        img = "<img class='img-fluid rounded-3 mb-2' src='" + assetsPath + 'img/elements/' + el.getAttribute('data-image') + "'>";
      }
      el.textContent = '';
      if (el.getAttribute('data-badge') !== undefined && el.getAttribute('data-badge-text') !== undefined) {
        el.insertAdjacentHTML(
          'afterbegin',
          renderHeader(el.getAttribute('data-badge'), el.getAttribute('data-badge-text')) + img + element
        );
      }
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

  // prevent sidebar to open onclick dropdown buttons of tasks
  const tasksItemDropdown = [].slice.call(document.querySelectorAll('.kanban-tasks-item-dropdown'));
  if (tasksItemDropdown) {
    tasksItemDropdown.forEach(function (e) {
      e.addEventListener('click', function (el) {
        el.stopPropagation();
      });
    });
  }

  // Toggle add new input and actions add-new-btn
  if (kanbanAddBoardBtn) {
    kanbanAddBoardBtn.addEventListener('click', () => {
      kanbanAddNewInput.forEach(el => {
        el.value = '';
        el.classList.toggle('d-none');
      });
    });
  }

  // Render add new inline with boards
  if (kanbanContainer) {
    kanbanContainer.appendChild(kanbanAddNewBoard);
  }

  // Makes kanban title editable for rendered boards
  if (kanbanTitleBoard) {
    kanbanTitleBoard.forEach(function (elem) {
      elem.addEventListener('mouseenter', function () {
        this.contentEditable = 'true';
      });

      // Appends delete icon with title
      elem.insertAdjacentHTML('afterend', renderBoardDropdown());
    });
  }

  // To delete Board for rendered boards
  const deleteBoards = [].slice.call(document.querySelectorAll('.delete-board'));
  if (deleteBoards) {
    deleteBoards.forEach(function (elem) {
      elem.addEventListener('click', function () {
        const id = this.closest('.kanban-board').getAttribute('data-id');
        kanban.removeBoard(id);
      });
    });
  }

  // Delete task for rendered boards
  const deleteTask = [].slice.call(document.querySelectorAll('.delete-task'));
  if (deleteTask) {
    deleteTask.forEach(function (e) {
      e.addEventListener('click', function () {
        const id = this.closest('.kanban-item').getAttribute('data-eid');
        kanban.removeElement(id);
      });
    });
  }

  // Cancel btn add new input
  const cancelAddNew = document.querySelector('.kanban-add-board-cancel-btn');
  if (cancelAddNew) {
    cancelAddNew.addEventListener('click', function () {
      kanbanAddNewInput.forEach(el => {
        el.classList.toggle('d-none');
      });
    });
  }

  // Add new board
  if (kanbanAddNewBoard) {
    kanbanAddNewBoard.addEventListener('submit', function (e) {
      e.preventDefault();
      const thisEle = this,
        value = thisEle.querySelector('.form-control').value,
        id = value.replace(/\s+/g, '-').toLowerCase();
      kanban.addBoards([
        {
          id: id,
          title: value
        }
      ]);

      // Adds delete board option to new board, delete new boards & updates data-order
      const kanbanBoardLastChild = document.querySelectorAll('.kanban-board:last-child')[0];
      if (kanbanBoardLastChild) {
        const header = kanbanBoardLastChild.querySelector('.kanban-title-board');
        header.insertAdjacentHTML('afterend', renderBoardDropdown());

        // To make newly added boards title editable
        kanbanBoardLastChild.querySelector('.kanban-title-board').addEventListener('mouseenter', function () {
          this.contentEditable = 'true';
        });
      }

      // Add delete event to delete newly added boards
      const deleteNewBoards = kanbanBoardLastChild.querySelector('.delete-board');
      if (deleteNewBoards) {
        deleteNewBoards.addEventListener('click', function () {
          const id = this.closest('.kanban-board').getAttribute('data-id');
          kanban.removeBoard(id);
        });
      }

      // Remove current append new add new form
      if (kanbanAddNewInput) {
        kanbanAddNewInput.forEach(el => {
          el.classList.add('d-none');
        });
      }

      // To place inline add new btn after clicking add btn
      if (kanbanContainer) {
        kanbanContainer.appendChild(kanbanAddNewBoard);
      }
    });
  }
})();

function createColumn(boardId, title) {
  fetch('/coluna/criar/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({ board_id: boardId, title: title, order: 0 })
  })
    .then(response => response.json())
    .then(data => {
      if (data.id) {
        // Adiciona a coluna ao Kanban
        console.log('Coluna criada:', data);
      }
    })
    .catch(error => console.error('Erro ao criar coluna:', error));
}

function updateColumn(columnId, newTitle, newOrder) {
  fetch(`/coluna/${columnId}/atualizar/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({ title: newTitle, order: newOrder })
  })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        // Atualiza a coluna no Kanban
        console.log('Coluna atualizada:', data);
      }
    })
    .catch(error => console.error('Erro ao atualizar coluna:', error));
}

function deleteColumn(columnId) {
  fetch(`/coluna/${columnId}/deletar/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken')
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        // Remove a coluna do Kanban
        console.log('Coluna deletada:', columnId);
      }
    })
    .catch(error => console.error('Erro ao deletar coluna:', error));
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
