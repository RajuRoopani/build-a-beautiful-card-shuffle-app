# Task Management Dashboard

A lightweight, browser-based task management application built with vanilla HTML, CSS, and JavaScript. No frameworks, no build tools, no backend server — just open `index.html` in your browser and start managing your tasks.

---

## Features

- **View Tasks** — See all your tasks in a scrollable sidebar list with status indicators
- **Filter by Status** — Quick filter buttons to view All, To Do, In Progress, or Done tasks
- **Task Details** — Click any task to view its full description, creation date, and current status
- **Create Tasks** — Add new tasks via a modal form with title and description
- **Change Status** — Update task status using a dropdown in the detail panel
- **Status Badges** — Color-coded badges (🔴 todo, 🟡 in-progress, 🟢 done) for quick visual identification
- **Responsive Layout** — Two-column desktop design that adapts to your screen size
- **No Setup Required** — Works immediately in any modern browser; in-memory data resets on refresh

---

## Getting Started

### Prerequisites
- A modern web browser (Chrome, Firefox, Safari, or Edge)
- That's it! No Node.js, no Python, no dependencies to install.

### Installation
Simply clone the repository and open `index.html` in your browser:

```bash
git clone https://github.com/RajuRoopani/build-a-task-management-dashboard.git
cd build-a-task-management-dashboard
open index.html
```

Or if you prefer to use a local web server:

```bash
# Python 3
python -m http.server 8000

# Node.js with http-server
npx http-server

# Then visit http://localhost:8000 in your browser
```

---

## Usage

### Quick Walkthrough

1. **Open the App** — Launch `index.html` in your browser
   - The dashboard loads with 3 sample tasks (one for each status)

2. **Browse Tasks** — View tasks in the left sidebar
   - Each task shows its title and a color-coded status badge

3. **Filter Tasks** — Click the filter buttons at the top of the sidebar
   - Select **All** to see everything
   - Select **To Do**, **In Progress**, or **Done** to filter by status

4. **View Details** — Click a task to see its full information
   - The right panel displays the title, description, and creation date
   - A dropdown allows you to change the status immediately

5. **Create a Task** — Click the **+ New Task** button in the header
   - Fill in the title (required) and description (optional)
   - Click **Create** to add the task
   - The new task appears in the sidebar and is automatically selected

6. **Update Status** — Select a task and use the status dropdown in the detail panel
   - Changes are reflected immediately in the sidebar badges

### Important Notes

- **In-Memory Storage** — All tasks live in your browser's memory
- **No Persistence** — Refreshing the page resets to the original 3 sample tasks
- **No Sync** — Tasks are not saved to a server or localStorage
- This is perfect for quick task planning sessions or demonstrating the UI

---

## Project Structure

```
.
├── index.html          — Semantic HTML markup with dialog for the modal form
├── style.css           — CSS Grid layout, Flexbox styling, and color-coded badges
├── app.js              — Complete application logic with Revealing Module Pattern
└── README.md           — This file
```

### File Descriptions

| File | Purpose |
|------|---------|
| **index.html** | Declares the page structure, links CSS/JS, and provides semantic DOM elements for the sidebar, detail panel, and modal |
| **style.css** | All visual styling including CSS Grid (2-column layout), Flexbox (internal arrangement), color schemes, and responsive design |
| **app.js** | Application logic: data store, task management (add/update/filter), rendering functions, and event delegation |
| **README.md** | Setup instructions and feature overview |

---

## Technical Details

### Architecture

The application uses the **Revealing Module Pattern** — a clean, ES5-compatible approach that avoids global namespace pollution without requiring a build step.

```
app.js Structure:
├── STORE
│   ├── Task data array (3 seed tasks)
│   ├── Active filter state
│   └── Active task selection
│
├── SIDEBAR
│   └── Render task list with current filter applied
│
├── DETAIL PANEL
│   └── Render selected task or empty state
│
├── MODAL
│   ├── Form input validation
│   └── Task creation handler
│
├── FILTERS
│   └── Filter button state management
│
├── EVENT WIRING
│   └── Single delegated click handler for all user interactions
│
└── INIT
    └── Bootstrap rendering and event listeners
```

### Layout Strategy

- **CSS Grid** — Two-column layout (fixed sidebar + fluid main area) fills the entire viewport
- **Flexbox** — Used within each column for internal arrangement
- **Native `<dialog>`** — Modern HTML modal element (no jQuery, no manual z-index management)
- **Mobile-Friendly** — Sidebar takes priority on smaller screens

```
┌─────────────────────────────────────────┐
│  Header: Task Dashboard  [+ New Task]  │
├──────────────────┬──────────────────────┤
│  [Filters]       │                      │
│  ─────────────── │  Task Details        │
│  □ Task A  todo  │  (title, status,     │
│  □ Task B  prog  │   description)       │
│  □ Task C  done  │                      │
│                  │                      │
└──────────────────┴──────────────────────┘
┌─────────────────────────────────────────┐
│  Modal (centered overlay, when open)   │
└─────────────────────────────────────────┘
```

### Data Model

Each task is a plain JavaScript object:

```js
{
  id:          String,        // Unique identifier (e.g. "seed-1")
  title:       String,        // Task name (max 100 chars)
  description: String,        // Details (optional)
  status:      "todo" | "in-progress" | "done",
  createdDate: String         // ISO 8601 timestamp
}
```

### Browser Support

- ✅ Chrome 37+
- ✅ Firefox 98+
- ✅ Safari 15.4+
- ✅ Edge 79+

(Requires `<dialog>` element support, available in all modern browsers)

### Performance

- **Rendering** — Full re-render of each section (sidebar, detail panel) on state changes
- **Data Scale** — Optimized for ~50–200 tasks; no virtual scrolling needed at this scale
- **Memory** — All state held in a single JS array; no localStorage or API calls
- **Load Time** — Instant; all code loads synchronously in ~10ms

---

## Seed Data

The application comes with 3 sample tasks to demonstrate the interface:

```js
1. "Set up project repository" — Status: Done
   Description: Initialize the GitHub repo, add README and folder structure.
   Created: 2025-01-10T09:00:00.000Z

2. "Design wireframes" — Status: In Progress
   Description: Create low-fidelity wireframes for the dashboard layout.
   Created: 2025-01-12T11:30:00.000Z

3. "Write unit tests" — Status: To Do
   Description: Add tests for task CRUD operations and filter logic.
   Created: 2025-01-14T08:00:00.000Z
```

---

## Accessibility

- **Semantic HTML** — Uses `<aside>`, `<main>`, `<dialog>`, and proper heading hierarchy
- **Focus Management** — Modal traps focus inside the dialog element
- **Screen Readers** — Active task indicated with `aria-selected`, badges use `aria-label`
- **Keyboard Navigation** — All controls are keyboard-accessible via native focus behavior

---

## Customization

### Changing the Sample Data

Edit the `tasks` array at the top of `app.js`:

```js
const tasks = [
  {
    id: "your-id-1",
    title: "Your Task Title",
    description: "Your description",
    status: "todo",
    createdDate: new Date().toISOString(),
  },
  // ... more tasks
];
```

### Styling

All styles are in `style.css`. Key customization points:

- **Color scheme** — Look for CSS variables or `.status-todo`, `.status-in-progress`, `.status-done` classes
- **Layout dimensions** — Sidebar width and header height are defined in the grid template
- **Fonts** — Set in the `body` rule using system fonts

### Adding Persistence

To save tasks to localStorage, modify `app.js`:

```js
// After adding/updating a task:
localStorage.setItem('dashboard-tasks', JSON.stringify(tasks));

// On app init, load saved data:
const saved = localStorage.getItem('dashboard-tasks');
if (saved) tasks = JSON.parse(saved);
```

---

## Limitations & Future Ideas

### Current Limitations

- **In-Memory Only** — Data resets on refresh
- **No Sync** — Single-user, single-device
- **No Edit** — Can only view and change status, not modify title/description
- **Limited Validation** — Basic checks on form input

### Ideas for Enhancement

- [ ] LocalStorage persistence
- [ ] Edit existing tasks (title/description)
- [ ] Drag-and-drop to reorder tasks
- [ ] Search/filter by text
- [ ] Dark mode toggle
- [ ] Subtasks or checklists
- [ ] Tags/labels
- [ ] Due dates with notifications
- [ ] Export tasks as CSV or JSON

---

## Development

### Running Tests

Currently, the app includes no formal test suite. To add tests, create a `tests/` directory with Jasmine, Jest, or Vitest and test the exposed functions from `app.js`.

### Code Style

- **No Linter Required** — Vanilla JS with clear conventions
- **Comments** — Inline comments explain complex logic
- **Naming** — Function names are descriptive (e.g., `renderSidebar()`, `selectTask()`)
- **No Build Step** — Single `<script>` tag in HTML loads everything

### Making Changes

1. Edit HTML markup in `index.html`
2. Update styles in `style.css`
3. Implement logic in `app.js`
4. Open `index.html` in your browser to test
5. Use browser DevTools (F12) to debug

---

## Troubleshooting

### Tasks Are Disappearing After Refresh
**Expected behavior!** This app uses in-memory storage only. To persist data, see "Adding Persistence" in the Customization section.

### Modal Won't Close
Make sure your browser supports the native `<dialog>` element. Check your browser version (Chrome 37+, Firefox 98+, Safari 15.4+, Edge 79+).

### Styles Not Applying
1. Ensure `style.css` is in the same directory as `index.html`
2. Clear your browser cache (Ctrl+Shift+Delete or Cmd+Shift+Delete)
3. Check the browser console for CSS load errors

### JavaScript Errors in Console
1. Check that `app.js` is in the same directory as `index.html`
2. Open DevTools (F12) and review the console for specific errors
3. Ensure you're using a modern browser (see Browser Support above)

---

## Browser DevTools Tips

- **Console** — Errors and `console.log()` output
- **Elements/Inspector** — Inspect the DOM structure
- **Network** — Verify CSS and JS files load correctly
- **Performance** — Profile rendering if the app feels slow

---

## Contributing

Improvements and suggestions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Test thoroughly in a browser
5. Commit and push
6. Open a pull request with a clear description

---

## License

MIT License — Feel free to use, modify, and distribute this project.

---

## Credits

Built by [Team Claw](https://github.com/RajuRoopani) — an autonomous multi-agent AI development team.

For the full architecture and design documentation, see [`docs/task-dashboard-design.md`](docs/task-dashboard-design.md).
