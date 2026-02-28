/**
 * Card Shuffle App — app.js
 * Pure vanilla JS, no framework, no build step.
 *
 * Architecture: Revealing-module IIFE with a strict state machine.
 *   States: 'idle' → 'shuffling' → 'revealing' → 'idle'
 *
 * Sections:
 *   1.  Constants & Card Data Model
 *   2.  State Machine
 *   3.  DOM References
 *   4.  Deck Rendering
 *   5.  Controls State (updateControls / updateStats)
 *   6.  Shuffle Animation (Fisher-Yates + CSS class choreography)
 *   7.  Card Reveal
 *   8.  Reset
 *   9.  Event Wiring
 *   10. Init
 */

(function () {
  'use strict';

  // ─── 1. CONSTANTS & CARD DATA MODEL ────────────────────────────────────────

  /** Four suits with their display glyph and color class. */
  var SUITS = [
    { name: 'Spades',   symbol: '♠', color: 'black' },
    { name: 'Hearts',   symbol: '♥', color: 'red'   },
    { name: 'Diamonds', symbol: '♦', color: 'red'   },
    { name: 'Clubs',    symbol: '♣', color: 'black' },
  ];

  /** Thirteen ranks with their display label. */
  var RANKS = [
    { value: 1,  label: 'A'  },
    { value: 2,  label: '2'  },
    { value: 3,  label: '3'  },
    { value: 4,  label: '4'  },
    { value: 5,  label: '5'  },
    { value: 6,  label: '6'  },
    { value: 7,  label: '7'  },
    { value: 8,  label: '8'  },
    { value: 9,  label: '9'  },
    { value: 10, label: '10' },
    { value: 11, label: 'J'  },
    { value: 12, label: 'Q'  },
    { value: 13, label: 'K'  },
  ];

  /**
   * Build the canonical 52-card deck.
   * Returns an Array of card objects:
   *   { rank: String, rankValue: Number, suit: String, symbol: String, color: String, id: String }
   */
  function buildDeck() {
    var deck = [];
    SUITS.forEach(function (suit) {
      RANKS.forEach(function (rank) {
        deck.push({
          rank:      rank.label,
          rankValue: rank.value,
          suit:      suit.name,
          symbol:    suit.symbol,
          color:     suit.color,
          id:        rank.label + '_' + suit.name,
        });
      });
    });
    return deck; // 52 cards
  }

  /**
   * Fisher-Yates shuffle — mutates the array in place and returns it.
   * Guaranteed uniform randomness.
   */
  function shuffleDeck(deck) {
    for (var i = deck.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var temp = deck[i];
      deck[i] = deck[j];
      deck[j] = temp;
    }
    return deck;
  }

  // ─── 2. STATE MACHINE ───────────────────────────────────────────────────────

  /**
   * Valid states:
   *   'idle'      – waiting for user interaction
   *   'shuffling' – spread/fan/reassemble animation running
   *   'revealing' – card flip/zoom animation running
   */
  var STATES = { IDLE: 'idle', SHUFFLING: 'shuffling', REVEALING: 'revealing' };

  var state = {
    current:     STATES.IDLE,
    deck:        buildDeck(),   // canonical ordered deck (shuffled in place on each click)
    revealedCard: null,         // last card shown to the user
    stats: {
      drawn:     0,  // total cards revealed this session
      shuffles:  0,  // total shuffles performed
    },
  };

  /** Transition to a new state and update UI guards. */
  function setState(newState) {
    state.current = newState;
    updateControls();
  }

  // ─── 3. DOM REFERENCES ─────────────────────────────────────────────────────

  var deckStack   = document.getElementById('deck-stack');
  var revealCard  = document.getElementById('reveal-card');
  var revealFront = document.getElementById('reveal-front');
  var revealBack  = document.getElementById('reveal-back');
  var revealLabel = document.getElementById('reveal-label');
  var btnShuffle  = document.getElementById('btn-shuffle');
  var btnReset    = document.getElementById('btn-reset');

  // Stats bar elements
  var statDrawn     = document.getElementById('stat-drawn');
  var statRemaining = document.getElementById('stat-remaining');
  var statShuffles  = document.getElementById('stat-shuffles');
  var deckCountEl   = document.getElementById('deck-count');

  // ─── 4. DECK RENDERING ─────────────────────────────────────────────────────

  /** Total cards in a standard deck. */
  var DECK_SIZE = 52;

  /**
   * Render the stacked deck into #deck-stack.
   *
   * The number of rendered card elements reflects how many remain undrawn,
   * giving a tactile "pile shrinks as you draw" effect.
   *
   * Cards are absolutely positioned with tiny x/y offsets for a 3-D pile
   * feel.  We cap the visual step at 26 to avoid a messy overhang.
   *
   * @param {number} [count] — how many cards to render (default: DECK_SIZE).
   */
  function renderDeck(count) {
    var cardsToRender = (typeof count === 'number') ? count : DECK_SIZE;
    deckStack.innerHTML = '';

    if (cardsToRender <= 0) {
      // Deck exhausted — show an empty-pile placeholder.
      var empty = document.createElement('div');
      empty.className = 'deck-empty-placeholder';
      empty.setAttribute('aria-label', 'Deck is empty');
      empty.textContent = '✕';
      deckStack.appendChild(empty);
      deckStack.classList.add('deck--empty');
      return;
    }

    deckStack.classList.remove('deck--empty');

    for (var i = 0; i < cardsToRender; i++) {
      var el = document.createElement('div');
      el.className = 'card card--back';
      el.setAttribute('data-index', i);
      el.setAttribute('aria-hidden', 'true');

      // Slight staggered offset for depth illusion (max ~8 px shift total).
      var offset = Math.min(i, 26);
      el.style.setProperty('--stack-offset', offset);

      // Stack via z-index — top card has highest index.
      el.style.zIndex = i;

      // Inner content — card back design.
      el.innerHTML =
        '<div class="card-inner">' +
          '<div class="card-back-face"></div>' +
        '</div>';

      deckStack.appendChild(el);
    }
  }

  // ─── 5. CONTROLS STATE ─────────────────────────────────────────────────────

  /** Enable/disable buttons based on current state and deck exhaustion. */
  function updateControls() {
    var isIdle      = state.current === STATES.IDLE;
    var isDepleted  = state.stats.drawn >= 52;

    // Shuffle is blocked during animations AND when all 52 cards have been drawn.
    btnShuffle.disabled = !isIdle || isDepleted;
    // Reset is only useful once at least one card has been drawn.
    btnReset.disabled   = !isIdle || state.stats.drawn === 0;

    btnShuffle.classList.toggle('btn--loading',   !isIdle && !isDepleted);
    btnShuffle.classList.toggle('btn--depleted',  isDepleted);

    // Update the shuffle button label to communicate deck-exhausted state.
    var btnIcon = btnShuffle.querySelector('.btn-icon');
    if (isDepleted) {
      btnShuffle.setAttribute('aria-label', 'Deck exhausted — reset to play again');
      if (btnIcon) btnIcon.textContent = '🃏';
      // Swap button text node (last child text node)
      btnShuffle.childNodes[btnShuffle.childNodes.length - 1].textContent = ' Deck Empty';
    } else {
      btnShuffle.setAttribute('aria-label', 'Shuffle deck and draw a random card');
      if (btnIcon) btnIcon.textContent = '🎴';
      btnShuffle.childNodes[btnShuffle.childNodes.length - 1].textContent = ' Shuffle & Draw';
    }
  }

  /**
   * Refresh all stats bar counters and the deck-count label.
   * remaining = 52 - drawn (each shuffle draws 1 card; reset clears drawn).
   */
  function updateStats() {
    var remaining = 52 - state.stats.drawn;
    if (statDrawn)     statDrawn.textContent     = state.stats.drawn;
    if (statRemaining) statRemaining.textContent = remaining;
    if (statShuffles)  statShuffles.textContent  = state.stats.shuffles;
    if (deckCountEl)   deckCountEl.textContent   = remaining;

    // Keep the deck-stack ARIA label current for screen readers.
    if (deckStack) {
      deckStack.setAttribute(
        'aria-label',
        remaining > 0
          ? 'Shuffled card deck — ' + remaining + ' cards remaining'
          : 'Deck exhausted — reset to play again'
      );
    }

    // Animate stat change with a brief highlight class (CSS defines the keyframe).
    [statDrawn, statRemaining, statShuffles].forEach(function (el) {
      if (!el) return;
      el.classList.remove('stat-value--bump');
      // Trigger reflow so removing + re-adding the class restarts the animation.
      void el.offsetWidth;
      el.classList.add('stat-value--bump');
    });
  }

  // ─── 6. SHUFFLE ANIMATION ──────────────────────────────────────────────────

  /**
   * Main entry point: shuffle the deck and reveal a card.
   * Animation timeline (all durations in ms):
   *   0       — setState(shuffling), disable button
   *   0-400   — fan cards out (spread class added)
   *   400-700 — hold spread
   *   700-1100— reassemble (spread class removed, reassemble class added)
   *   1100    — reveal phase begins
   */
  function startShuffle() {
    if (state.current !== STATES.IDLE) return; // guard against rapid clicks
    if (state.stats.drawn >= 52) return;        // guard: deck is exhausted
    setState(STATES.SHUFFLING);

    // Step 1: reset any previously revealed card
    resetRevealedCard();

    // Step 2: physically shuffle the deck array and increment shuffle count
    shuffleDeck(state.deck);
    state.stats.shuffles += 1;
    updateStats();

    // Step 3: fan cards out
    deckStack.classList.add('deck--spread');

    // Step 4: After spread, reassemble
    setTimeout(function () {
      deckStack.classList.remove('deck--spread');
      deckStack.classList.add('deck--reassemble');
    }, 700);

    // Step 5: After reassemble, trigger reveal
    setTimeout(function () {
      deckStack.classList.remove('deck--reassemble');
      pickAndRevealCard();
    }, 1300);
  }

  // ─── 7. CARD REVEAL ────────────────────────────────────────────────────────

  /**
   * Pick a random card from the shuffled deck and animate it face-up.
   * Uses the top of the already-shuffled deck (index 0) for true randomness
   * driven by Fisher-Yates — each shuffle guarantees a different order.
   */
  function pickAndRevealCard() {
    setState(STATES.REVEALING);

    // Pick top card of the shuffled deck
    var card = state.deck[0];
    state.revealedCard = card;

    // Track drawn count (cap at DECK_SIZE so stats don't go negative).
    if (state.stats.drawn < DECK_SIZE) {
      state.stats.drawn += 1;
    }
    updateStats();

    // Re-render deck pile to show it shrinking as cards are drawn.
    renderDeck(DECK_SIZE - state.stats.drawn);

    // Populate the reveal card faces
    populateRevealCard(card);

    // Unhide the reveal area and trigger entrance animation
    revealCard.removeAttribute('aria-hidden');
    revealCard.classList.remove('reveal-card--exit');

    // Small delay so the browser paints the hidden state before animating in
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        revealCard.classList.add('reveal-card--visible');
        revealCard.classList.add('reveal-card--flip');
      });
    });

    // Update the label with accessible text
    revealLabel.textContent = card.rank + ' of ' + card.suit;

    // Return to idle after reveal animation completes
    setTimeout(function () {
      setState(STATES.IDLE);
    }, 900);
  }

  /**
   * Build the card face HTML for the large reveal card.
   * Shows rank in top-left, large suit symbol in centre, rank in bottom-right.
   */
  function populateRevealCard(card) {
    var colorClass = 'card--' + card.color; // e.g. card--red, card--black

    // Update front face — BEM class card-face--front + color modifier
    revealFront.className = 'card-face card-face--front ' + colorClass;
    revealFront.setAttribute('aria-label', 'Revealed card: ' + card.rank + ' of ' + card.suit);
    revealFront.innerHTML =
      '<div class="card-corner card-corner--top">' +
        '<span class="card-rank">' + card.rank   + '</span>' +
        '<span class="card-suit">' + card.symbol + '</span>' +
      '</div>' +
      '<span class="card-center-suit" aria-hidden="true">' + card.symbol + '</span>' +
      '<div class="card-corner card-corner--bottom">' +
        '<span class="card-rank">' + card.rank   + '</span>' +
        '<span class="card-suit">' + card.symbol + '</span>' +
      '</div>';

    // Update back face — BEM class card-face--back (matches HTML)
    revealBack.className = 'card-face card-face--back';
    revealBack.innerHTML = '<div class="card-back-pattern"></div>';

    // Apply color modifier to the outer flip container for CSS theming.
    // Strip any existing color modifier first to avoid class accumulation.
    revealCard.className = revealCard.className
      .replace(/\bcard--(?:red|black)\b/g, '')
      .replace(/\s{2,}/g, ' ')
      .trim() + ' ' + colorClass;
  }

  /**
   * Hide and reset the previously revealed card (with exit animation).
   * AC24: smooth exit before new shuffle begins.
   */
  function resetRevealedCard() {
    if (state.revealedCard === null) return;

    revealCard.classList.remove('reveal-card--visible', 'reveal-card--flip');
    revealCard.classList.add('reveal-card--exit');
    revealLabel.textContent = '';

    // After exit animation, fully hide the element
    setTimeout(function () {
      revealCard.classList.remove('reveal-card--exit');
      revealCard.setAttribute('aria-hidden', 'true');
    }, 400);

    state.revealedCard = null;
  }

  // ─── 8. RESET ──────────────────────────────────────────────────────────────

  /**
   * Reset: hide the revealed card, rebuild an ordered 52-card deck,
   * re-render the full pile, and clear the drawn counter.
   *
   * Intentional design choice: `stats.shuffles` is NOT reset — it
   * reflects the total number of shuffles performed this session,
   * which is more interesting to the user than per-deck count.
   */
  function resetApp() {
    if (state.current !== STATES.IDLE) return;

    resetRevealedCard();
    state.deck = buildDeck();
    state.stats.drawn = 0;
    renderDeck(DECK_SIZE);   // full 52-card pile
    updateStats();
    updateControls();
  }

  // ─── 9. EVENT WIRING ───────────────────────────────────────────────────────

  /**
   * Handle keydown on a button — activate on Enter or Space.
   * Native <button> already handles this, but we add it explicitly for
   * any host environment that might intercept default key behaviour.
   */
  function handleButtonKey(action) {
    return function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        action();
      }
    };
  }

  function bindEvents() {
    btnShuffle.addEventListener('click', startShuffle);
    btnReset.addEventListener('click', resetApp);

    // Explicit keyboard bindings (belt-and-suspenders for native <button>)
    btnShuffle.addEventListener('keydown', handleButtonKey(startShuffle));
    btnReset.addEventListener('keydown', handleButtonKey(resetApp));

    // Clicking the deck stack also triggers shuffle (nice UX touch).
    // Guard: same conditions as the button — idle state and deck not exhausted.
    deckStack.addEventListener('click', function () {
      if (state.current === STATES.IDLE && state.stats.drawn < DECK_SIZE) {
        startShuffle();
      }
    });
  }

  // ─── 10. INIT ──────────────────────────────────────────────────────────────

  function init() {
    renderDeck();
    updateStats();
    updateControls();

    // Hide the reveal card initially
    revealCard.setAttribute('aria-hidden', 'true');
    revealLabel.textContent = '';

    bindEvents();
  }

  // Boot when DOM is ready (script has defer, but this guard is belt-and-suspenders)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
