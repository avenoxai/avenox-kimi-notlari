(function () {
  'use strict';

  var form = document.getElementById('task-form');
  var titleInput = document.getElementById('task-title');
  var priorityInput = document.getElementById('task-priority');
  var dueInput = document.getElementById('task-due');
  var filtersEl = document.getElementById('filters');
  var searchInput = document.getElementById('search');
  var sortSelect = document.getElementById('sort');
  var listEl = document.getElementById('task-list');
  var emptyEl = document.getElementById('empty-state');
  var countAll = document.getElementById('count-all');
  var countActive = document.getElementById('count-active');
  var countDone = document.getElementById('count-done');

  var PRIORITY_LABEL = { 'düşük': 'Düşük', 'orta': 'Orta', 'yüksek': 'Yüksek' };
  var PRIORITY_CLASS = { 'düşük': 'low', 'orta': 'mid', 'yüksek': 'high' };

  function formatDue(value) {
    if (!value) return '';
    var parts = value.split('-');
    if (parts.length !== 3) return value;
    return parts[2] + '.' + parts[1] + '.' + parts[0];
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function taskMarkup(task) {
    var due = formatDue(task.due);
    var meta = '<span class="pill ' + PRIORITY_CLASS[task.priority] + '">' + PRIORITY_LABEL[task.priority] + '</span>';
    if (due) meta += '<span class="due">' + due + '</span>';

    return '<li class="task' + (task.done ? ' is-done' : '') + '" data-id="' + task.id + '">' +
      '<label class="check">' +
        '<input type="checkbox" data-action="toggle"' + (task.done ? ' checked' : '') + ' />' +
      '</label>' +
      '<div class="task-body">' +
        '<span class="task-title" data-action="edit" title="Düzenlemek için çift tıkla">' + escapeHtml(task.title) + '</span>' +
        '<div class="task-meta">' + meta + '</div>' +
      '</div>' +
      '<button type="button" class="remove" data-action="delete" title="Sil">&times;</button>' +
    '</li>';
  }

  function renderCounts(list) {
    var doneCount = list.filter(function (task) { return task.done; }).length;
    countAll.textContent = list.length;
    countActive.textContent = list.length - doneCount;
    countDone.textContent = doneCount;
  }

  function render() {
    var list = Store.visibleTasks();
    listEl.innerHTML = list.map(taskMarkup).join('');
    emptyEl.hidden = list.length > 0;
    renderCounts(Store.state.tasks);
  }

  function taskIdFrom(element) {
    var row = element.closest('.task');
    if (!row) return null;
    return parseInt(row.getAttribute('data-id'), 10);
  }

  function titleOf(id) {
    var tasks = Store.state.tasks;
    for (var i = 0; i < tasks.length; i++) {
      if (tasks[i].id === id) return tasks[i].title;
    }
    return '';
  }

  function startEdit(titleEl, id) {
    var input = document.createElement('input');
    input.type = 'text';
    input.className = 'edit-input';
    input.value = titleOf(id);

    titleEl.replaceWith(input);
    input.focus();
    input.select();

    var closed = false;

    function commit() {
      if (closed) return;
      closed = true;
      Store.editTask(id, input.value);
      render();
    }

    function cancel() {
      if (closed) return;
      closed = true;
      render();
    }

    input.addEventListener('blur', commit);
    input.addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        commit();
      } else if (event.key === 'Escape') {
        event.preventDefault();
        cancel();
      }
    });
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    var title = titleInput.value.trim();
    if (!title) {
      titleInput.focus();
      return;
    }
    Store.addTask(title, priorityInput.value, dueInput.value);
    titleInput.value = '';
    dueInput.value = '';
    priorityInput.value = 'orta';
    titleInput.focus();
    render();
  });

  listEl.addEventListener('change', function (event) {
    if (event.target.getAttribute('data-action') !== 'toggle') return;
    var id = taskIdFrom(event.target);
    if (id === null) return;
    Store.toggleTask(id);
    render();
  });

  listEl.addEventListener('click', function (event) {
    var target = event.target.closest('[data-action="delete"]');
    if (!target) return;
    var id = taskIdFrom(target);
    if (id === null) return;
    Store.deleteTask(id);
    render();
  });

  listEl.addEventListener('dblclick', function (event) {
    var target = event.target.closest('[data-action="edit"]');
    if (!target) return;
    var id = taskIdFrom(target);
    if (id === null) return;
    startEdit(target, id);
  });

  filtersEl.addEventListener('click', function (event) {
    var button = event.target.closest('.filter');
    if (!button) return;

    var buttons = filtersEl.querySelectorAll('.filter');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].classList.toggle('is-active', buttons[i] === button);
    }

    Store.setFilter(button.getAttribute('data-filter'));
    render();
  });

  searchInput.addEventListener('input', function (event) {
    Store.setQuery(event.target.value);
    render();
  });

  sortSelect.addEventListener('change', function (event) {
    Store.setSort(event.target.value);
    render();
  });

  Store.load();
  render();
})();
