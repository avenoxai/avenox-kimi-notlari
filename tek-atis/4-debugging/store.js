(function (global) {
  'use strict';

  var STORAGE_KEY = 'yapilacaklar.tasks.v1';

  var state = {
    tasks: [],
    filter: 'all',
    query: '',
    sort: 'created'
  };

  var SEED = [
    { id: 1, title: 'Fatura ödemelerini kontrol et', priority: 'yüksek', due: '2026-10-02', done: false },
    { id: 2, title: 'Haftalık rapor taslağını hazırla', priority: 'orta', due: '2026-09-24', done: false },
    { id: 3, title: 'Spor salonu üyeliğini yenile', priority: 'düşük', due: '', done: false },
    { id: 4, title: 'Sunum slaytlarını gözden geçir', priority: 'yüksek', due: '2026-09-22', done: true },
    { id: 5, title: 'Yeni klavye siparişi ver', priority: 'düşük', due: '2026-11-15', done: false },
    { id: 6, title: 'Ekip toplantısı notlarını paylaş', priority: 'orta', due: '', done: true },
    { id: 7, title: 'Sigorta poliçelerini karşılaştır', priority: 'orta', due: '2026-09-30', done: false },
    { id: 8, title: 'Kitaplığı yeniden düzenle', priority: 'düşük', due: '', done: false }
  ];

  var PRIORITY_RANK = { 'yüksek': 1, 'orta': 2, 'düşük': 3 };

  function readStorage() {
    try {
      var raw = global.localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : null;
    } catch (err) {
      return null;
    }
  }

  function save() {
    try {
      global.localStorage.setItem(STORAGE_KEY, JSON.stringify(state.tasks));
    } catch (err) {
      // depolama kapaliysa uygulama bellekte calismaya devam eder
    }
  }

  function nextId() {
    var maxId = 0;
    for (var i = 0; i < state.tasks.length; i++) {
      var id = state.tasks[i].id;
      if (typeof id === 'number' && id > maxId) maxId = id;
    }
    return maxId + 1;
  }

  function normalizeIds() {
    var seen = {};
    var changed = false;
    for (var i = 0; i < state.tasks.length; i++) {
      var id = state.tasks[i].id;
      if (typeof id !== 'number' || seen[id]) {
        state.tasks[i].id = nextId();
        changed = true;
      }
      seen[state.tasks[i].id] = true;
    }
    if (changed) save();
  }

  function load() {
    var stored = readStorage();
    if (stored) {
      state.tasks = stored;
      normalizeIds();
      return state.tasks;
    }
    state.tasks = SEED.map(function (item) {
      return { id: item.id, title: item.title, priority: item.priority, due: item.due, done: item.done };
    });
    save();
    return state.tasks;
  }

  function findTask(id) {
    for (var i = 0; i < state.tasks.length; i++) {
      if (state.tasks[i].id === id) return state.tasks[i];
    }
    return null;
  }

  function addTask(title, priority, due) {
    var clean = String(title).trim();
    if (!clean) return null;

    var task = {
      id: nextId(),
      title: clean,
      priority: priority || 'orta',
      due: due || '',
      done: false
    };

    state.tasks.push(task);
    save();
    return task;
  }

  function toggleTask(id) {
    var task = findTask(id);
    if (!task) return;
    task.done = !task.done;
    save();
  }

  function editTask(id, title) {
    var task = findTask(id);
    if (!task) return;
    var clean = String(title).trim();
    if (!clean) return;
    task.title = clean;
    save();
  }

  function deleteTask(id) {
    for (var i = 0; i < state.tasks.length; i++) {
      if (state.tasks[i].id === id) {
        state.tasks.splice(i, 1);
        save();
        return;
      }
    }
  }

  function filterTasks(filter) {
    if (filter === 'active') {
      return state.tasks.filter(function (task) { return !task.done; });
    }
    if (filter === 'done') {
      return state.tasks.filter(function (task) { return task.done; });
    }
    return state.tasks.slice();
  }

  function searchTasks(list, query) {
    var needle = query.trim().toLocaleLowerCase('tr');
    return list.filter(function (task) {
      return task.title.toLocaleLowerCase('tr').indexOf(needle) !== -1;
    });
  }

  function sortTasks(list, mode) {
    if (mode === 'priority') {
      return list.slice().sort(function (a, b) {
        return (PRIORITY_RANK[a.priority] || 2) - (PRIORITY_RANK[b.priority] || 2);
      });
    }
    if (mode === 'due') {
      return list.slice().sort(function (a, b) {
        if (!a.due && !b.due) return 0;
        if (!a.due) return 1;
        if (!b.due) return -1;
        if (a.due < b.due) return -1;
        if (a.due > b.due) return 1;
        return 0;
      });
    }
    if (mode === 'created') {
      return list.slice().sort(function (a, b) { return a.id - b.id; });
    }
    return list;
  }

  function visibleTasks() {
    var list = filterTasks(state.filter);
    if (state.query.trim()) {
      list = searchTasks(list, state.query);
    }
    return sortTasks(list, state.sort);
  }

  global.Store = {
    state: state,
    load: load,
    addTask: addTask,
    toggleTask: toggleTask,
    editTask: editTask,
    deleteTask: deleteTask,
    visibleTasks: visibleTasks,
    setFilter: function (value) { state.filter = value; },
    setQuery: function (value) { state.query = value; },
    setSort: function (value) { state.sort = value; }
  };
})(window);
