# Card Shuffle App

A beautiful, single-page card shuffle application with casino aesthetics, smooth animations, and accessible design. Shuffle a 52-card deck with the Fisher-Yates algorithm and see each card revealed with a stunning 3D flip effect.

## Features

- **Fisher-Yates Shuffle** — Guaranteed uniform randomness, no algorithmic bias
- **Animated Card Reveal** — 3D flip effect with smooth entrance/exit animations
- **Casino Green Felt Aesthetic** — Deep forest green (#1B4332) with warm gold accents, reminiscent of luxury casinos
- **CSS-Only Card Back Pattern** — Crosshatch design on navy background (no images, no SVGs)
- **Stats Tracking** — Real-time counters for cards drawn, cards remaining, and total shuffles
- **Deck Depletion Tracking** — Visual display of remaining cards in the deck
- **Reset Deck Functionality** — Instantly rebuild the deck and reset session stats
- **Fully Responsive** — Mobile-first design with `600px` breakpoint (side-by-side desktop, stacked mobile)
- **ARIA-Accessible** — Screen reader announcements, keyboard-operable buttons, semantic HTML, live regions
- **No External Dependencies** — Pure vanilla HTML5, CSS3, and JavaScript (ES5 IIFE pattern). No build step, no server required.

## Tech Stack

- **HTML5** — Semantic markup with ARIA roles, labels, and live regions
- **CSS3** — Custom properties, `@keyframes` animations, 3D transforms, `preserve-3d`
- **JavaScript (ES5)** — IIFE module pattern, state machine architecture, DOM manipulation
- **No Frameworks** — Lightweight, fast, zero dependencies

## File Structure

```
index.html          Single-file app: HTML structure + <style> (casino theme, animations, responsive) + <script> (state machine, Fisher-Yates shuffle, animation orchestration)
README.md           Project documentation (this file)
```

## How to Run

1. **Open `index.html` in any modern browser:**
   ```bash
   # On macOS / Linux
   open index.html
   
   # On Windows
   start index.html
   
   # Or just double-click the file in your file manager
   ```

2. **Click "Shuffle & Draw"** to shuffle the deck and reveal a random card
3. **Click "Reset Deck"** to rebuild the deck and reset stats
4. **Click the deck stack itself** as a shortcut to trigger a shuffle

No build step, no dependencies — just open the file and play.

## Design Decisions

### Color Palette
- **Deep Casino Green** (`#1B4332`) — App background, evokes Vegas luxury
- **Warm Gold** (`#F0C040`) — Primary button color, accents (high contrast, premium feel)
- **Warm White** (`#FAFAF5`) — Card face background (readable, not pure white)
- **Card Red** (`#C0392B`) — Hearts and Diamonds suit color
- **Card Black** (`#1a1a2e`) — Spades and Clubs suit color
- **Navy Back** (`#1a1a6e`) — Card back base with crosshatch pattern

### Typography
- **Georgia, serif** — Card content (rank, suit) — traditional, casino-like
- **system-ui, sans-serif** — UI chrome (buttons, stats, labels) — modern, readable
- **No external font imports** — Georgia is universally available, no FOUT risk

### Card Back Pattern
CSS-only crosshatch design (45° + -45° repeating gradients) on navy:
```css
repeating-linear-gradient(45deg, ...)   /* forward slash */
repeating-linear-gradient(-45deg, ...)  /* backslash */
background-color: #1a1a6e;              /* navy base */
```
No images or SVGs needed — pure CSS for instant load time.

### Card Aspect Ratio
**5:7** (standard poker card dimensions)
- Desktop: 160px × 224px (reveal card), ~100px × 140px (deck cards)
- Mobile: 120px × 168px (reveal card), ~80px × 112px (deck cards)

### Pure CSS Animations
- **Deck spread** — 400ms, fans cards outward via `transform: rotate()` and `translate()`
- **Deck reassemble** — 600ms, pulls cards back together with easing
- **Card flip** — 600ms, uses `rotateY()` with `preserve-3d` and `backface-visibility`
- **Card entrance** — 300ms, scales and fades in
- **Card exit** — 400ms, scales and fades out
- **No GSAP or animation libraries** — all effects use native CSS `@keyframes` and `transition`

## Accessibility

### Semantic HTML
- Proper heading hierarchy (`<h1>`, `<h2>`)
- ARIA roles: `role="banner"`, `role="img"`, `role="region"`, `role="button"`
- Alt text and aria-labels on all interactive elements

### Screen Reader Support
- `aria-label` on buttons: "Shuffle deck and draw a random card"
- `aria-live="polite"` on reveal area — announces each new card drawn
- `aria-atomic="true"` on card elements — provides full context to screen readers
- Reveal label updates announce card rank and suit (e.g., "Ace of Spades")

### Keyboard Navigation
- All buttons are native `<button>` elements — fully keyboard operable
- `Enter` and `Space` trigger buttons natively
- `:focus` styles with gold outline for clear focus indicator
- Deck stack click is keyboard-accessible via button alternative

### Focus Management
- Focus indicators visible in all states
- Loading/disabled states clearly communicated
- Tab order follows visual layout (left to right, top to bottom)

## Browser Support

Modern browsers with support for:
- CSS custom properties (`--color-*`)
- `transform-style: preserve-3d` (3D CSS transforms)
- `@keyframes` animations
- `requestAnimationFrame()` (JS animation orchestration)

**Tested on:**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Architecture Overview

### State Machine
```
Idle → Shuffling → Revealing → Idle
```
- **Idle** — Waiting for user interaction, buttons enabled
- **Shuffling** — Deck spread/reassemble animations running, buttons disabled
- **Revealing** — Card flip animation running, buttons disabled

### Data Model
```js
state = {
  current: 'idle',
  deck: [...52 cards...],           // Shuffled in place each round
  revealedCard: {...card object...},
  stats: {
    drawn: 0,     // Cards revealed this session
    shuffles: 0   // Times shuffled this session
  }
}
```

### Fisher-Yates Shuffle
Classic uniform-randomness shuffle (O(n) time, optimal):
```js
for (var i = deck.length - 1; i > 0; i--) {
  var j = Math.floor(Math.random() * (i + 1));
  // swap deck[i] and deck[j]
}
```

### Animation Timeline
Each "Shuffle & Draw" cycle:
1. **0ms** — setState(shuffling), disable buttons
2. **0–400ms** — Fan deck spread outward (`deck--spread` class)
3. **400–700ms** — Hold spread for visual effect
4. **700–1100ms** — Reassemble deck (`deck--reassemble` class)
5. **1100ms** — Trigger card reveal
6. **1100–1700ms** — Card flip + zoom into reveal area (`reveal-card--flip` class)
7. **1700ms** — Return to idle, re-enable buttons

## Responsive Design

### Desktop (≥ 600px)
- Deck and reveal area side-by-side in flexbox
- Larger card dimensions (160×224px reveal, 100×140px deck)
- Buttons stacked vertically in footer
- 40px padding on stage sides

### Mobile (< 600px)
- Deck and reveal area stacked vertically
- Smaller card dimensions (120×168px reveal, 80×112px deck)
- Buttons full-width
- 16px padding on stage sides
- Single-column layout, touch-friendly tap targets

## Stats Bar

Located at the bottom of the app:
- **Drawn** — How many cards have been revealed this session
- **Remaining** — 52 minus drawn (updates after each shuffle)
- **Shuffles** — How many times "Shuffle & Draw" has been clicked

All counters reset to 0 when "Reset Deck" is clicked.

## Development

### Local Testing
Simply open `index.html` in your browser. No localhost server needed.

### Code Quality
- **Strict mode** — `'use strict'` in IIFE prevents accidental global scope pollution
- **Cross-browser compatible** — No ES6+, uses ES5 syntax for wide browser support
- **Well-commented** — Code sections clearly marked with visual dividers
- **No console logs** — Clean DevTools, suitable for production

### Adding New Features
The state machine and IIFE pattern make it easy to extend:
1. Add new state enum to `STATES` object
2. Add state transition logic in event handlers
3. Create new animation CSS classes and `@keyframes`
4. Wire DOM selectors and event listeners in `bindEvents()`

## Known Limitations

- **No persistent deck depletion** — Each "Shuffle & Draw" reshuffles all 52 cards. If true depletion (not reshuffling mid-session) is desired, the game logic would need to track a draw pile separately.
- **No sound effects** — Pure visual experience (could add Web Audio API, but out of scope for v1)
- **No mobile swipe gestures** — Buttons and click/tap only (could add touch events in future)
- **No progressive Web App (PWA) support** — No service worker for offline play (could add manifest + SW for offline capability)

## License

Open source. Feel free to fork, modify, and use in personal or commercial projects.

## Credits

- **Architect** — UI/UX design spec and semantic HTML structure
- **Senior Dev 1** — JavaScript state machine, shuffle algorithm, animation orchestration
- **Senior Dev 2** — CSS styling, casino aesthetic, 3D transforms and animations
- **Junior Dev 1** — README documentation

---

**Enjoy the shuffle.** 🎰
