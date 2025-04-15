$(document).ready(function () {
  // Obtém e faz o parse do JSON do textarea
  var $stepsTextArea = $('#id_steps');
  var stepsData = [];
  try {
    stepsData = JSON.parse($stepsTextArea.val());
  } catch (e) {
    console.error("Erro ao parsear JSON:", e);
  }

  // Oculta o textarea original
  $stepsTextArea.hide();

  // Cria os contêineres para a visualização em tabela e para edição do JSON
  var $tableEditor = $('<div id="table-editor"></div>');
  var $jsonEditor = $(
    '<div id="json-editor" style="display: none;">' +
      '<textarea id="json-textarea" class="form-control" rows="10"></textarea>' +
    '</div>'
  );

  // Cria o toggleSwitch (switch do Bootstrap)
  var $toggleSwitch = $(
    '<div class="form-check form-switch">' +
      '<input class="form-check-input" type="checkbox" id="toggle-view">' +
      '<label class="form-check-label" for="toggle-view">Visualizar como JSON</label>' +
    '</div>'
  );
  
  // Cria um header global para manter o título e o switch sempre visíveis
  var $headerContainer = $('<div class="d-flex justify-content-between align-items-center mb-3"></div>');
  var $title = $('<h3 id="table-container-title">Editor de Etapas</h3>');
  $headerContainer.append($title).append($toggleSwitch);
  
  // Insere os elementos na página
  $stepsTextArea.after($jsonEditor);
  $stepsTextArea.after($tableEditor);
  // Insere o header global acima dos editores
  $tableEditor.before($headerContainer);

  // Variável para controlar a visualização atual
  var currentView = 'table';

  // Função que renderiza o editor em tabela (exceto o header que permanece fixo)
  function renderTableEditor() {
    $tableEditor.empty();
    $tableEditor.append('<p>Para adicionar uma nova etapa, clique no botão "Adicionar etapa".</p>');
    $tableEditor.append('<p>Edite as etapas abaixo. As alterações serão refletidas no JSON.</p>');
    var table = $(
      '<div class="table-responsive">' +
        '<table class="table table-bordered text-nowrap">' +
          '<thead>' +
            '<tr>' +
              '<th>ID</th>' +
              '<th>ID da Etapa</th>' +
              '<th>Nome da Etapa</th>' +
              '<th>ID do Usuário</th>' +
              '<th>Descrição</th>' +
              '<th>Dependências</th>' +
              '<th>Finalizado?</th>' +
              '<th>Prazo (em dias)</th>' +
              '<th>Grupos permitidos</th>' +
              '<th>Data de Conclusão</th>' +
              '<th>Tipo de Conteúdo</th>' +
              '<th>ID do Objeto</th>' +
              '<th>Ações</th>' +
            '</tr>' +
          '</thead>' +
          '<tbody></tbody>' +
        '</table>' +
      '</div>' +
      '<p><strong>Nota:</strong> Campos vazios serão considerados como null.</p>' +
      '<p><strong>Nota:</strong> IDs de dependências e grupos permitidos devem ser separados por vírgula.</p>'
    );
    var tbody = table.find('tbody');

    // Cria uma linha para cada etapa
    $.each(stepsData, function (index, step) {
      var tr = $('<tr></tr>');
      tr.append('<td>' + step.id + '</td>');
      tr.append('<td><input type="number" class="step-step-id form-control" value="' + (step.step ? step.step.id : '') + '"></td>');
      tr.append('<td><input style="width: 200px" type="text" class="step-step-name form-control" value="' + (step.step ? step.step.name : '') + '"></td>');
      tr.append('<td><input type="text" class="step-user_id form-control" value="' + (step.user_id !== null ? step.user_id : '') + '"></td>');
      tr.append('<td><input style="width: 250px" type="text" class="step-description form-control" value="' + step.description + '"></td>');
      tr.append('<td><input type="text" class="step-dependencies form-control" value="' + (step.dependencies.join(',') || '') + '"></td>');
      var isCompleted = step.is_completed ? 'checked' : '';
      tr.append('<td><input type="checkbox" class="step-is_completed" ' + isCompleted + '></td>');
      tr.append('<td><input type="number" class="step-deadline_days form-control" value="' + step.deadline_days + '"></td>');
      tr.append('<td><input type="text" class="step-allowed_groups form-control" value="' + (step.allowed_groups.join(',') || '') + '"></td>');
      tr.append('<td><input style="width: 180px" type="text" class="step-completion_date form-control" value="' + (step.completion_date || '') + '"></td>');
      tr.append('<td><input type="number" class="step-content_type form-control" value="' + (step.content_type !== null ? step.content_type : '') + '"></td>');
      tr.append('<td><input type="number" class="step-object_id form-control" value="' + (step.object_id !== null ? step.object_id : '') + '"></td>');

      // Ações: mover para cima, mover para baixo e remover
      var moveUpDisabled = (index === 0) ? 'disabled' : '';
      var moveDownDisabled = (index === stepsData.length - 1) ? 'disabled' : '';
      var actionsHtml =
        '<button type="button" class="move-up btn btn-secondary btn-sm" ' + moveUpDisabled + '>↑</button> ' +
        '<button type="button" class="move-down btn btn-secondary btn-sm" ' + moveDownDisabled + '>↓</button> ' +
        '<button type="button" class="remove-step btn btn-danger btn-sm">Remover</button>';
      tr.append('<td>' + actionsHtml + '</td>');
      
      tbody.append(tr);
    });

    $tableEditor.append(table);
    $tableEditor.append('<button type="button" id="add-step" class="btn btn-success">Adicionar etapa</button>');
  }

  // Renderiza o editor em tabela inicialmente
  renderTableEditor();

  // Atualiza o JSON antes de submeter o formulário
  $('form').on('submit', function () {
    if (currentView === 'json') {
      try {
        stepsData = JSON.parse($('#json-textarea').val());
      } catch(e) {
        alert("Erro no JSON. Verifique a sintaxe antes de salvar.");
        return false;
      }
    }
    $stepsTextArea.val(JSON.stringify(stepsData));
  });

  // Alterna entre as visualizações, mantendo o header com o switch visível
  $toggleSwitch.find('#toggle-view').on('change', function () {
    if (this.checked) {
      $tableEditor.find('tbody tr').each(function (index) {
        var row = $(this);
        stepsData[index].step.id = parseInt(row.find('.step-step-id').val(), 10) || 0;
        stepsData[index].step.name = row.find('.step-step-name').val();
        var userVal = row.find('.step-user_id').val();
        stepsData[index].user_id = (userVal === "" ? null : userVal);
        stepsData[index].description = row.find('.step-description').val();
  
        var deps = row.find('.step-dependencies').val().split(',').map(function (val) {
          val = val.trim();
          return val === "" ? null : Number(val);
        }).filter(function (val) { return val !== null; });
        stepsData[index].dependencies = deps;
  
        stepsData[index].is_completed = row.find('.step-is_completed').is(':checked');
        stepsData[index].deadline_days = parseInt(row.find('.step-deadline_days').val(), 10) || 0;
        var groups = row.find('.step-allowed_groups').val().split(',').map(function (val) {
          return val.trim();
        }).filter(function (val) { return val !== ""; });
        stepsData[index].allowed_groups = groups;
        var compDate = row.find('.step-completion_date').val();
        stepsData[index].completion_date = (compDate === "" ? null : compDate);
        var contentType = row.find('.step-content_type').val();
        stepsData[index].content_type = (contentType === "" ? null : parseInt(contentType, 10));
        var objectId = row.find('.step-object_id').val();
        stepsData[index].object_id = (objectId === "" ? null : parseInt(objectId, 10));
      });
      
      $('#json-textarea').val(JSON.stringify(stepsData, null, 2));
      $tableEditor.hide();
      $jsonEditor.show();
      currentView = 'json';
    } else {
      try {
        var newData = JSON.parse($('#json-textarea').val());
        stepsData = newData;
      } catch (e) {
        alert("Erro no JSON. Verifique a sintaxe antes de mudar para a visualização em tabela.");
        $(this).prop('checked', true);
        return;
      }
      renderTableEditor();
      $jsonEditor.hide();
      $tableEditor.show();
      currentView = 'table';
    }
  });
  
  // Eventos no editor em tabela (adicionar, remover, mover, atualizar)
  $tableEditor.on('click', '#add-step', function () {
    var newId = stepsData.length ? Math.max.apply(null, stepsData.map(function (s) { return s.id; })) + 1 : 1;
    var newStep = {
      id: newId,
      step: { id: newId, name: "" },
      user_id: null,
      description: "",
      dependencies: [],
      is_completed: false,
      deadline_days: 0,
      allowed_groups: [],
      completion_date: null,
      content_type: null,
      object_id: null
    };
    stepsData.push(newStep);
    renderTableEditor();
  });

  $tableEditor.on('click', '.remove-step', function () {
    var rowIndex = $(this).closest('tr').index();
    stepsData.splice(rowIndex, 1);
    renderTableEditor();
  });

  $tableEditor.on('click', '.move-up', function () {
    var rowIndex = $(this).closest('tr').index();
    if (rowIndex > 0) {
      var temp = stepsData[rowIndex];
      stepsData[rowIndex] = stepsData[rowIndex - 1];
      stepsData[rowIndex - 1] = temp;
      renderTableEditor();
    }
  });

  $tableEditor.on('click', '.move-down', function () {
    var rowIndex = $(this).closest('tr').index();
    if (rowIndex < stepsData.length - 1) {
      var temp = stepsData[rowIndex];
      stepsData[rowIndex] = stepsData[rowIndex + 1];
      stepsData[rowIndex + 1] = temp;
      renderTableEditor();
    }
  });

  $tableEditor.on('change', 'input', function () {
    var row = $(this).closest('tr');
    var index = row.index();
    stepsData[index].step.id = parseInt(row.find('.step-step-id').val(), 10) || 0;
    stepsData[index].step.name = row.find('.step-step-name').val();
    var userVal = row.find('.step-user_id').val();
    stepsData[index].user_id = (userVal === "" ? null : userVal);
    stepsData[index].description = row.find('.step-description').val();

    var deps = row.find('.step-dependencies').val().split(',').map(function (val) {
      val = val.trim();
      return val === "" ? null : Number(val);
    }).filter(function (val) { return val !== null; });
    stepsData[index].dependencies = deps;

    stepsData[index].is_completed = row.find('.step-is_completed').is(':checked');
    stepsData[index].deadline_days = parseInt(row.find('.step-deadline_days').val(), 10) || 0;
    var groups = row.find('.step-allowed_groups').val().split(',').map(function (val) {
      return val.trim();
    }).filter(function (val) { return val !== ""; });
    stepsData[index].allowed_groups = groups;
    var compDate = row.find('.step-completion_date').val();
    stepsData[index].completion_date = (compDate === "" ? null : compDate);
    var contentType = row.find('.step-content_type').val();
    stepsData[index].content_type = (contentType === "" ? null : parseInt(contentType, 10));
    var objectId = row.find('.step-object_id').val();
    stepsData[index].object_id = (objectId === "" ? null : parseInt(objectId, 10));
  });
});
