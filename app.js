// Task Management Dashboard — Application Logic
// Revealing Module Pattern (IIFE), no framework, no build step.

(function () {
  'use strict';

  // ── STORE ──────────────────────────────────────────────────────────
  const tasks = [
    {
      id: 'seed-1',
      title: 'Set up project repository',
      description: 'Initialise the GitHub repo, add README and folder structure.',
      status: 'done',
      createdDate: '2025-01-10T09:00:00.000Z',
    },
    {
      id: 'seed-2',
      title: 'Design wireframes',
      description: 'Create low-fidelity wireframes for the dashboard layout.',
      status: 'in-progress',
      createdDate: '2025-01-12T11:30:00.000Z',
    },
    {
      id: 'seed-3',
      title: 'Write unit tests',
      description: 'Add tests for task CRUD operations and filter logic.',
      status: 'todo',
      createdDate: '2025-01-14T08:00:00.000Z',
    },
  ];

  let activeTaskId = null;
  let activeFilter = 'all';

  /** Return tasks that match the current activeFilter. */
  function getFilteredTasks() {
    if (activeFilter === 'all') return tasks;
    return tasks.filter(function (t) { return t.status === activeFilter; });
  }

  /** Find a single task by id, or undefined. */
  function getTaskById(id) {
    return tasks.find(function (t) { return t.id === id; });
  }

  /** Create a new task, push it to the store, and return it. */
  function addTask(data) {
    var task = {
      id: typeof crypto !== 'undefined' && crypto.randomUUID
        ? crypto.randomUUID()
        : Date.now().toString(),
      title: data.title.trim(),
      description: (data.description || '').trim(),
      status: 'todo',
      createdDate: new Date().toISOString(),
    };
    tasks.push(task);
    return task;
  }

  /** Mutate a task's status in place. */
  function updateTaskStatus(id, newStatus) {
    var task = getTaskById(id);
    if (task) task.status = newStatus;
  }

  // ── DOM REFERENCES ─────────────────────────────────────────────────
  var filterBar    = document.getElementById('filter-bar');
  var taskList     = document.getElementById('task-list');
  var detailPanel  = document.getElementById('detail-panel');
  var modal        = document.getElementById('task-modal');
  var form         = document.getElementById('task-form');
  var openModalBtn = document.getElementById('open-modal-btn');
  var cancelBtn    = document.getElementById('modal-cancel-btn');
  var titleInput   = document.getElementById('task-title');
  var descInput    = document.getElementById('task-description');

  // ── FILTERS ────────────────────────────────────────────────────────
  var FILTERS = ['all', 'todo', 'in-progress', 'done'];

  /** Render filter buttons into #filter-bar. */
  function renderFilters() {
    filterBar.innerHTML = FILTERS.map(function (f) {
      var label = f === 'all' ? 'All'
        : f === 'todo' ? 'To Do'
        : f === 'in-progress' ? 'In Progress'
        : 'Done';
      var cls = 'filter-btn' + (f === activeFilter ? ' active' : '');
      return '<button type="button" class="' + cls + '" data-filter="' + f + '">' + label + '</button>';
    }).join('');
  }

  /** Set the active filter and re-render. */
  function setFilter(value) {
    activeFilter = value;
    // If the currently-selected task is hidden by the new filter, deselect it
    if (activeTaskId) {
      var visible = getFilteredTasks();
      var still = visible.some(function (t) { return t.id === activeTaskId; });
      if (!still) activeTaskId = null;
    }
    renderFilters();
    renderSidebar();
    renderDetail();
  }

  // ── SIDEBAR ────────────────────────────────────────────────────────

  /** Render the task list in the sidebar from getFilteredTasks(). */
  function renderSidebar() {
    var filtered = getFilteredTasks();
    if (filtered.length === 0) {
      taskList.innerHTML = '<li class="empty-state" style="padding:24px;text-align:center;color:#95a5a6;font-size:13px;">No tasks match this filter.</li>';
      return;
    }
    taskList.innerHTML = filtered.map(function (t) {
      var isActive = t.id === activeTaskId;
      var cls = 'task-item' + (isActive ? ' active' : '');
      var badgeCls = 'status-badge status-badge--' + t.status;
      var badgeLabel = t.status === 'todo' ? 'To Do'
        : t.status === 'in-progress' ? 'In Progress'
        : 'Done';
      return '<li class="' + cls + '" data-task-id="' + t.id + '" role="option"' +
        (isActive ? ' aria-selected="true"' : ' aria-selected="false"') + '>' +
        '<span class="task-item-title">' + escapeHtml(t.title) + '</span>' +
        '<span class="' + badgeCls + '" aria-label="Status: ' + badgeLabel + '">' + badgeLabel + '</span>' +
        '</li>';
    }).join('');
  }

  /** Select a task and update views. */
  function selectTask(id) {
    activeTaskId = id;
    renderSidebar();
    renderDetail();
  }

  // ── DETAIL PANEL ───────────────────────────────────────────────────

  /** Render the detail panel for the active task, or an empty state. */
  function renderDetail() {
    if (!activeTaskId) {
      detailPanel.innerHTML =
        '<div class="empty-state">' +
          '<div class="empty-state-icon">\uD83D\uDCCB</div>' +
          '<div class="empty-state-title">No task selected</div>' +
          '<div class="empty-state-hint">Click a task in the sidebar to view details.</div>' +
        '</div>';
      return;
    }

    var task = getTaskById(activeTaskId);
    if (!task) {
      activeTaskId = null;
      renderDetail();
      return;
    }

    var created = new Date(task.createdDate).toLocaleDateString(undefined, {
      year: 'numeric', month: 'long', day: 'numeric',
    });

    var descHtml = task.description
      ? escapeHtml(task.description)
      : '<span class="muted">No description provided.</span>';

    detailPanel.innerHTML =
      '<h2>' + escapeHtml(task.title) + '</h2>' +

      '<div class="detail-field">' +
        '<span class="detail-field-label">Status</span>' +
        '<select class="status-select" data-action="change-status" aria-label="Change task status">' +
          statusOption('todo', 'To Do', task.status) +
          statusOption('in-progress', 'In Progress', task.status) +
          statusOption('done', 'Done', task.status) +
        '</select>' +
      '</div>' +

      '<div class="detail-field">' +
        '<span class="detail-field-label">Created</span>' +
        '<span class="detail-field-value">' + created + '</span>' +
      '</div>' +

      '<div class="detail-field">' +
        '<span class="detail-field-label">Description</span>' +
        '<div class="detail-field-value">' + descHtml + '</div>' +
      '</div>';

    // Bind the status dropdown change listener
    var sel = detailPanel.querySelector('.status-select');
    if (sel) {
      sel.addEventListener('change', function () {
        updateTaskStatus(activeTaskId, sel.value);
        renderSidebar();
        renderDetail();
      });
    }
  }

  /** Helper: build an <option> for the status dropdown. */
  function statusOption(value, label, current) {
    return '<option value="' + value + '"' + (value === current ? ' selected' : '') + '>' + label + '</option>';
  }

  // ── MODAL (Create Task) ────────────────────────────────────────────

  /** Open the create-task modal and reset form fields. */
  function openModal() {
    titleInput.value = '';
    descInput.value = '';
    modal.showModal();
    titleInput.focus();
  }

  /** Close the modal. */
  function closeModal() {
    modal.close();
  }

  /** Handle modal form submission: validate, add task, refresh views. */
  function handleModalSubmit(e) {
    e.preventDefault();

    var title = titleInput.value.trim();
    if (!title) {
      titleInput.focus();
      return;
    }

    var newTask = addTask({
      title: title,
      description: descInput.value,
    });

    closeModal();

    // If filter would hide the new task (status "todo"), switch filter to show it
    if (activeFilter !== 'all' && activeFilter !== 'todo') {
      activeFilter = 'all';
      renderFilters();
    }

    renderSidebar();
    selectTask(newTask.id);
  }

  // ── EVENT WIRING ───────────────────────────────────────────────────

  function bindEvents() {
    // Delegated click handler for sidebar tasks and filter buttons
    document.addEventListener('click', function (e) {
      // Task item click
      var taskItem = e.target.closest('[data-task-id]');
      if (taskItem) return selectTask(taskItem.dataset.taskId);

      // Filter button click
      var filterBtn = e.target.closest('[data-filter]');
      if (filterBtn) return setFilter(filterBtn.dataset.filter);

      // Open modal
      if (e.target.id === 'open-modal-btn' || e.target.closest('#open-modal-btn')) {
        return openModal();
      }

      // Cancel modal
      if (e.target.id === 'modal-cancel-btn' || e.target.closest('#modal-cancel-btn')) {
        return closeModal();
      }
    });

    // Form submit
    form.addEventListener('submit', handleModalSubmit);

    // Close modal on backdrop click (clicking the dialog element itself, not children)
    modal.addEventListener('click', function (e) {
      if (e.target === modal) closeModal();
    });

    // Close modal on Escape (native <dialog> does this, but ensure form isn't submitted)
    modal.addEventListener('cancel', function (e) {
      e.preventDefault();
      closeModal();
    });
  }

  // ── UTILITY ────────────────────────────────────────────────────────

  /** Minimal HTML escaping to prevent XSS in dynamic content. */
  function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // ── INIT ───────────────────────────────────────────────────────────

  function init() {
    renderFilters();
    renderSidebar();
    renderDetail();
    bindEvents();
  }

  // Kick off when the DOM is ready (script loaded with `defer`, so this fires
  // after parsing but we use DOMContentLoaded for extra safety).
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
