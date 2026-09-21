document.addEventListener("DOMContentLoaded", () => {
    // ==========================================
    // 1. CONTAINER & AUTHENTICATION CONTROLS (Main DOCX Script)
    // ==========================================
    const container = document.getElementById('container');
    const registerBtn = document.getElementById('register');
    const loginBtn = document.getElementById('login');

    if (registerBtn && container) {
        registerBtn.addEventListener('click', () => {
            container.classList.add("active");
        });
    }

    if (loginBtn && container) {
        loginBtn.addEventListener('click', () => {
            container.classList.remove("active");
        });
    }

    // Tab Switching Logic
    const tabSignin = document.getElementById('tab-signin');
    const tabSignup = document.getElementById('tab-signup');
    const formSignin = document.getElementById('form-signin');
    const formSignup = document.getElementById('form-signup');

    if (tabSignin && tabSignup) {
        tabSignin.addEventListener('click', () => {
            tabSignin.classList.add('active');
            tabSignup.classList.remove('active');
            if (formSignin) formSignin.classList.add('active');
            if (formSignup) formSignup.classList.remove('active');
        });

        tabSignup.addEventListener('click', () => {
            tabSignup.classList.add('active');
            tabSignin.classList.remove('active');
            if (formSignup) formSignup.classList.add('active');
            if (formSignin) formSignin.classList.remove('active');
        });
    }

    // 3D Tilt Effect on Hover
    const cards = document.querySelectorAll('.tilt-card, .bento-item, .metric-block-card, .subject-item-box-card');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = ((y - centerY) / centerY) * -12;
            const rotateY = ((x - centerX) / centerX) * 12;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(8px)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)`;
        });
    });

    // Initialize Dashboard Features
    initNavigationRouter();
    initActionEventListeners();
    renderBudgetTracker();
    renderSidebarFeed();
    renderTaskTracker();
    renderNotesTracker();
    renderFlashcardsGrid();
    renderScheduleTimetable();
});

// ==========================================
// 2. STATE MANAGEMENT & DASHBOARD LOGIC (App File Features)
// ==========================================
const appState = {
  budget: { total: 2000.00, spent: 0.00 },
  expenses: [],
  tasks: [
    { id: 1, title: "Calculus Assignment", deadline: "Sept.21", status: "soon" },
    { id: 2, title: "IT 5 Project", deadline: "Sept.24", status: "all" },
    { id: 3, title: "CCE 104 Reporting", deadline: "Sept.23", status: "all" }
  ],
  notes: [
    { id: 1, text: "1. Title sa notes dawg", tag: "School" },
    { id: 2, text: "2. Title sa notes dawg", tag: "Personal" },
    { id: 3, text: "3. Title sa notes dawg", tag: "Ideas" },
    { id: 4, text: "4. Title sa notes dawg", tag: "School" },
    { id: 5, text: "5. Title sa notes dawg", tag: "Pinned" }
  ],
  subjects: [
    { id: 1, name: "Calculus", page: 15, style: 'normal' },
    { id: 2, name: "IT 5", page: 15, style: 'grey' },
    { id: 3, name: "CCE 104", page: 15, style: 'outline' }
  ],
  schedule: {},
  activeTaskFilter: 'all',
  activeNotesFilter: 'all',
  sidebarRightTab: 'tasks'
};

function initNavigationRouter() {
  const navItems = document.querySelectorAll('.sidebar .nav-item');
  
  navItems.forEach(item => {
    item.addEventListener('click', function() {
      navItems.forEach(i => i.classList.remove('active'));
      this.classList.add('active');

      const targetId = this.getAttribute('data-target');
      const panels = document.querySelectorAll('main, .main-layout, .tab-content');
      panels.forEach(panel => {
        panel.classList.remove('active');
        panel.style.display = 'none';
      });

      const targetPanel = document.getElementById(targetId);
      if (targetPanel) {
        targetPanel.classList.add('active');
        targetPanel.style.display = 'flex';
      }
    });
  });
}

function renderBudgetTracker() {
  const lblTotal = document.getElementById('lbl-budget-total');
  const lblRemain = document.getElementById('lbl-budget-remain');
  const lblSpent = document.getElementById('lbl-budget-spent');
  const remaining = appState.budget.total - appState.budget.spent;
  
  if (lblTotal) lblTotal.innerText = `₱${appState.budget.total.toFixed(2)}`;
  if (lblRemain) lblRemain.innerText = `₱${remaining.toFixed(2)}`;
  if (lblSpent) lblSpent.innerText = `₱${appState.budget.spent.toFixed(2)}`;
}

function renderSidebarFeed() {
  const listFeed = document.getElementById('sidebar-feed-list');
  const taskCount = document.getElementById('sidebar-task-counter');
  const pendingTasks = appState.tasks.filter(t => t.status !== 'completed');
  
  if (taskCount) taskCount.innerText = pendingTasks.length;
  if (!listFeed) return;
  listFeed.innerHTML = '';
  
  if (appState.sidebarRightTab === 'tasks') {
    if (pendingTasks.length === 0) {
      listFeed.innerHTML = '<div style="text-align:center;font-size:13px;margin-top:20px;">All caught up!</div>';
      return;
    }
    pendingTasks.forEach(task => {
      listFeed.innerHTML += `<div class="list-row-item"><span>${task.title}</span><span class="task-date-badge">Due ${task.deadline}</span></div>`;
    });
  } else {
    if (appState.expenses.length === 0) {
      listFeed.innerHTML = '<div style="text-align:center;font-size:13px;margin-top:20px;">All caught up!</div>';
      return;
    }
    appState.expenses.forEach(exp => {
      listFeed.innerHTML += `<div class="list-row-item"><span>${exp.desc}</span><strong style="color:var(--text-dark);">-₱${exp.amount.toFixed(2)}</strong></div>`;
    });
  }
}

function renderTaskTracker() {
  const container = document.getElementById('master-task-container');
  const lblAll = document.getElementById('task-filter-all');
  const lblSoon = document.getElementById('task-filter-soon');

  if (lblAll) lblAll.innerText = `All Tasks(${appState.tasks.length})`;
  if (lblSoon) lblSoon.innerText = `Due Soon(${appState.tasks.filter(t => t.status === 'soon').length})`;
  if (!container) return;
  container.innerHTML = '';

  let filtered = appState.tasks;
  if (appState.activeTaskFilter === 'soon') filtered = appState.tasks.filter(t => t.status === 'soon');
  if (appState.activeTaskFilter === 'completed') filtered = appState.tasks.filter(t => t.status === 'completed');

  if (filtered.length === 0) {
    container.innerHTML = '<div style="text-align:center;color:var(--text-muted);margin-top:20px;">No matching tasks found.</div>';
    return;
  }

  filtered.forEach(task => {
    const isDone = task.status === 'completed';
    container.innerHTML += `
      <div class="task-strip-row ${isDone ? 'completed-state' : ''}">
        <span>${task.title}</span>
        <div style="display:flex; align-items:center; gap:12px;">
          <span class="task-date-badge">Due on ${task.deadline}</span>
          <input type="checkbox" ${isDone ? 'checked' : ''} data-id="${task.id}" class="task-state-chk">
        </div>
      </div>`;
  });

  container.querySelectorAll('.task-state-chk').forEach(chk => {
    chk.addEventListener('change', function() {
      const id = parseInt(this.getAttribute('data-id'));
      const t = appState.tasks.find(item => item.id === id);
      if (t) {
        t.status = t.status === 'completed' ? 'all' : 'completed';
        renderTaskTracker();
        renderSidebarFeed();
      }
    });
  });
}

function renderNotesTracker(searchFilter = '') {
  const container = document.getElementById('master-notes-list');
  if (!container) return;
  container.innerHTML = '';

  let filtered = appState.notes;
  if (appState.activeNotesFilter !== 'all') {
    filtered = appState.notes.filter(n => n.tag === appState.activeNotesFilter);
  }

  if (searchFilter.trim() !== '') {
    filtered = filtered.filter(n => n.text.toLowerCase().includes(searchFilter.toLowerCase()));
  }

  if (filtered.length === 0) {
    container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:10px;">Notebook entry empty.</div>';
    return;
  }

  filtered.forEach(note => {
    container.innerHTML += `<div class="note-item-tile"><span>${note.text}</span><span class="delete-note-cross" data-id="${note.id}">×</span></div>`;
  });

  container.querySelectorAll('.delete-note-cross').forEach(cross => {
    cross.addEventListener('click', function() {
      const id = parseInt(this.getAttribute('data-id'));
      appState.notes = appState.notes.filter(n => n.id !== id);
      const searchInp = document.getElementById('notes-search-field');
      renderNotesTracker(searchInp ? searchInp.value : '');
    });
  });
}

function renderFlashcardsGrid() {
  const container = document.getElementById('master-flashcards-grid');
  if (!container) return;
  container.innerHTML = '';

  appState.subjects.forEach(sub => {
    let backgroundStyle = '';
    let classOutline = '';
    if (sub.style === 'grey') backgroundStyle = 'background-color: #ededed;';
    if (sub.style === 'outline') classOutline = 'active-outline';

    container.innerHTML += `
      <div class="subject-item-box-card ${classOutline}" style="${backgroundStyle}">
        <span class="delete-subject-btn" data-id="${sub.id}">×</span>
        <h3>${sub.name}</h3>
        <p>Page:${sub.page}</p>
      </div>`;
  });

  container.innerHTML += `<div class="subject-item-box-card add-placeholder-style" id="trigger-add-subject"><h3 style="font-size:28px;">Add subject</h3><p style="margin-top:5px;">Add Page:</p></div>`;

  container.querySelectorAll('.delete-subject-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      appState.subjects = appState.subjects.filter(s => s.id !== parseInt(this.getAttribute('data-id')));
      renderFlashcardsGrid();
    });
  });

  const triggerAdd = document.getElementById('trigger-add-subject');
  if (triggerAdd) {
    triggerAdd.addEventListener('click', () => {
      const title = prompt("Enter Subject Title:");
      const pageNum = parseInt(prompt("Enter Page Target Counter:", "15") || "15");
      if (title) {
        appState.subjects.push({ id: Date.now(), name: title, page: pageNum, style: 'normal' });
        renderFlashcardsGrid();
      }
    });
  }
}

function renderScheduleTimetable() {
  document.querySelectorAll('.schedule-matrix-table tbody tr').forEach(row => {
    const timeSlot = row.getAttribute('data-time');
    row.querySelectorAll('td:not(.hour-tag)').forEach((cell, idx) => {
      const days = ["MON", "TUES", "WED", "THU", "FRI"];
      const dayKey = cell.getAttribute('data-day') || days[idx];
      const stateKey = `${dayKey}||${timeSlot}`;
      cell.innerText = appState.schedule[stateKey] || '';
    });
  });
}

function initActionEventListeners() {
  const logExpenseBtn = document.getElementById('btn-log-expense');
  if (logExpenseBtn) {
    logExpenseBtn.addEventListener('click', () => {
      const descInp = document.getElementById('exp-desc');
      const catInp = document.getElementById('exp-cat');
      const amtInp = document.getElementById('exp-amt');
      if (!descInp || !catInp || !amtInp) return;

      const val = parseFloat(amtInp.value || '0');
      if (!descInp.value.trim() || isNaN(val) || val <= 0) return;

      appState.budget.spent += val;
      appState.expenses.push({ desc: `${descInp.value.trim()} (${catInp.value})`, amount: val });
      descInp.value = '';
      amtInp.value = '0';
      renderBudgetTracker();
      renderSidebarFeed();
    });
  }

  const subtabTasks = document.getElementById('subtab-tasks');
  const subtabExpenses = document.getElementById('subtab-expenses');

  if (subtabTasks && subtabExpenses) {
    subtabTasks.addEventListener('click', function() {
      appState.sidebarRightTab = 'tasks';
      this.classList.add('active');
      subtabExpenses.classList.remove('active');
      renderSidebarFeed();
    });

    subtabExpenses.addEventListener('click', function() {
      appState.sidebarRightTab = 'expenses';
      this.classList.add('active');
      subtabTasks.classList.remove('active');
      renderSidebarFeed();
    });
  }

  const createTaskBtn = document.getElementById('btn-create-task');
  if (createTaskBtn) {
    createTaskBtn.addEventListener('click', () => {
      const titleInp = document.getElementById('task-title-input');
      const dateInp = document.getElementById('task-date-input');
      const soonCheck = document.getElementById('task-soon-checkbox');
      if (!titleInp || !dateInp || !titleInp.value.trim() || !dateInp.value.trim()) return;

      appState.tasks.push({ id: Date.now(), title: titleInp.value.trim(), deadline: dateInp.value.trim(), status: (soonCheck && soonCheck.checked) ? 'soon' : 'all' });
      titleInp.value = '';
      dateInp.value = '';
      if (soonCheck) soonCheck.checked = false;
      renderTaskTracker();
      renderSidebarFeed();
    });
  }

  const filterAll = document.getElementById('task-filter-all');
  const filterSoon = document.getElementById('task-filter-soon');
  const filterDone = document.getElementById('task-filter-done');

  if (filterAll) {
    filterAll.addEventListener('click', function() {
      document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      this.classList.add('active'); appState.activeTaskFilter = 'all'; renderTaskTracker();
    });
  }
  if (filterSoon) {
    filterSoon.addEventListener('click', function() {
      document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      this.classList.add('active'); appState.activeTaskFilter = 'soon'; renderTaskTracker();
    });
  }
  if (filterDone) {
    filterDone.addEventListener('click', function() {
      document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      this.classList.add('active'); appState.activeTaskFilter = 'completed'; renderTaskTracker();
    });
  }

  const notesSearch = document.getElementById('notes-search-field');
  if (notesSearch) {
    notesSearch.addEventListener('input', function() { renderNotesTracker(this.value); });
  }

  document.querySelectorAll('.tag-row-pill').forEach(pill => {
    pill.addEventListener('click', function() {
      document.querySelectorAll('.tag-row-pill').forEach(p => p.classList.remove('active'));
      this.classList.add('active');
      appState.activeNotesFilter = this.getAttribute('data-tag');
      renderNotesTracker();
    });
  });

  const addNoteBtn = document.getElementById('btn-trigger-add-note');
  if (addNoteBtn) {
    addNoteBtn.addEventListener('click', () => {
      const noteText = prompt("Type note text content:");
      if (noteText) {
        const activeTag = appState.activeNotesFilter === 'all' ? 'School' : appState.activeNotesFilter;
        appState.notes.push({ id: Date.now(), text: `${appState.notes.length + 1}. ${noteText}`, tag: activeTag });
        renderNotesTracker();
      }
    });
  }

  document.querySelectorAll('.schedule-matrix-table tbody td:not(.hour-tag)').forEach(cell => {
    cell.addEventListener('click', function() {
      const days = ["MON", "TUES", "WED", "THU", "FRI"];
      const rowEl = this.parentElement;
      const time = rowEl.getAttribute('data-time');
      let cellIndex = Array.prototype.indexOf.call(rowEl.cells, this);
      const day = days[cellIndex - 1] || days[0];
      const stateKey = `${day}||${time}`;
      
      const newClassValue = prompt(`Schedule class entry for ${day} at ${time}:`, this.innerText);
      if (newClassValue !== null) {
        appState.schedule[stateKey] = newClassValue.trim();
        renderScheduleTimetable();
      }
    });
  });
}