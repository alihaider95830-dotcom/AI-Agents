# Design System — Glassmorphism SaaS Dashboard

> A refined, monochromatic glassmorphism design language built for clarity, depth, and professional SaaS interfaces.

---

## 1. Philosophy

This design system is built around **layered depth** — the idea that UI elements float at distinct elevations above a rich, textured background. Glass surfaces reveal the layers beneath them, creating a sense of spatial hierarchy without relying on color as the primary differentiator. The palette is intentionally restrained: near-black backgrounds, white-tinted glass, and silver/zinc accents — letting content and data carry the weight.

**Core Principles:**
- **Depth over decoration** — elevation and blur replace heavy color usage
- **Restraint** — every element earns its place; no visual noise
- **Legibility first** — contrast and hierarchy are non-negotiable
- **Subtle motion** — transitions reinforce spatial logic, never distract

---

## 2. Color Palette

All colors are defined as CSS custom properties on `:root`.

### Base Surface Colors

| Token | Hex | Usage |
|---|---|---|
| `--bg-base` | `#0a0a0b` | Root background — the deepest layer |
| `--bg-subtle` | `#111113` | Page sections, sidebars |
| `--bg-muted` | `#18181b` | Card backgrounds behind glass |

### Glass Surface Colors

| Token | Value | Usage |
|---|---|---|
| `--glass-surface` | `rgba(255, 255, 255, 0.04)` | Default card/panel fill |
| `--glass-surface-hover` | `rgba(255, 255, 255, 0.07)` | Hovered card state |
| `--glass-surface-active` | `rgba(255, 255, 255, 0.10)` | Active / selected state |
| `--glass-elevated` | `rgba(255, 255, 255, 0.08)` | Modals, dropdowns, tooltips |
| `--glass-overlay` | `rgba(0, 0, 0, 0.50)` | Backdrop overlays |

### Border & Stroke

| Token | Value | Usage |
|---|---|---|
| `--border-dim` | `rgba(255, 255, 255, 0.05)` | Subtle dividers |
| `--border-default` | `rgba(255, 255, 255, 0.10)` | Default card borders |
| `--border-strong` | `rgba(255, 255, 255, 0.18)` | Focus rings, active borders |
| `--border-input` | `rgba(255, 255, 255, 0.12)` | Form inputs |

### Text Colors

| Token | Hex | Usage |
|---|---|---|
| `--text-primary` | `#f4f4f5` | Headlines, primary labels |
| `--text-secondary` | `#a1a1aa` | Body copy, descriptions |
| `--text-tertiary` | `#71717a` | Placeholders, metadata |
| `--text-disabled` | `#3f3f46` | Disabled states |
| `--text-inverse` | `#09090b` | Text on light/white surfaces |

### Accent (Monochrome)

| Token | Hex | Usage |
|---|---|---|
| `--accent-white` | `#ffffff` | Primary CTAs, highlights |
| `--accent-silver` | `#d4d4d8` | Secondary accents |
| `--accent-zinc` | `#52525b` | Tertiary accents, tags |

### Semantic Colors

| Token | Value | Usage |
|---|---|---|
| `--status-success` | `rgba(134, 239, 172, 0.15)` | Success states (muted green) |
| `--status-success-text` | `#86efac` | Success text |
| `--status-warning` | `rgba(253, 224, 71, 0.15)` | Warning states (muted yellow) |
| `--status-warning-text` | `#fde047` | Warning text |
| `--status-error` | `rgba(252, 165, 165, 0.15)` | Error states (muted red) |
| `--status-error-text` | `#fca5a5` | Error text |
| `--status-info` | `rgba(147, 197, 253, 0.15)` | Info states (muted blue) |
| `--status-info-text` | `#93c5fd` | Info text |

---

## 3. Typography

Font stack uses a refined editorial pairing — a geometric display for headings, a neutral mono for data/code.

```css
/* Import */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

--font-sans: 'DM Sans', sans-serif;
--font-mono: 'DM Mono', monospace;
```

### Type Scale

| Token | Size | Weight | Line Height | Usage |
|---|---|---|---|---|
| `--text-xs` | `11px` | 400 | 1.5 | Labels, badges |
| `--text-sm` | `13px` | 400 | 1.5 | Secondary body, captions |
| `--text-base` | `15px` | 400 | 1.6 | Primary body copy |
| `--text-md` | `17px` | 500 | 1.5 | Card titles, nav items |
| `--text-lg` | `20px` | 500 | 1.4 | Section headings |
| `--text-xl` | `26px` | 600 | 1.3 | Page headings |
| `--text-2xl` | `34px` | 600 | 1.2 | Hero headings |
| `--text-3xl` | `46px` | 300 | 1.1 | Display / marketing |

### Usage Rules

- **Display text** — Light weight (300), letter-spacing `-0.03em`
- **Headings** — Semibold (600), letter-spacing `-0.02em`
- **Body** — Regular (400), letter-spacing `0`
- **Labels / UI** — Medium (500), letter-spacing `0.01em`, uppercase for small tags
- **Code / Data** — `DM Mono`, size matched to context

---

## 4. Glassmorphism Specifications

The core visual language. All glass components must follow these rules to maintain visual coherence.

### Glass Layer System

```
Layer 0 — Background    z-index: 0    No blur
Layer 1 — Base Glass    z-index: 10   blur(12px)
Layer 2 — Elevated      z-index: 20   blur(20px)
Layer 3 — Floating      z-index: 30   blur(28px)  (modals, dropdowns)
Layer 4 — Top           z-index: 40   blur(40px)  (tooltips, toasts)
```

### Glass Surface Recipe

```css
/* Base Card — Layer 1 */
.glass-card {
  background: var(--glass-surface);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow:
    0 1px 1px rgba(0, 0, 0, 0.12),
    0 4px 8px rgba(0, 0, 0, 0.24),
    0 8px 24px rgba(0, 0, 0, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

/* Elevated Panel — Layer 2 */
.glass-elevated {
  background: var(--glass-elevated);
  backdrop-filter: blur(20px) saturate(200%);
  -webkit-backdrop-filter: blur(20px) saturate(200%);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-xl);
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.20),
    0 8px 20px rgba(0, 0, 0, 0.30),
    0 20px 60px rgba(0, 0, 0, 0.20),
    inset 0 1px 0 rgba(255, 255, 255, 0.10);
}

/* Floating Modal — Layer 3 */
.glass-modal {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(28px) saturate(220%);
  -webkit-backdrop-filter: blur(28px) saturate(220%);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: var(--radius-2xl);
  box-shadow:
    0 4px 8px rgba(0, 0, 0, 0.30),
    0 16px 40px rgba(0, 0, 0, 0.40),
    0 40px 80px rgba(0, 0, 0, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
}
```

### Glass Rules

1. **Never use glass on glass** — glass components must always have a rich, textured background behind them to blur against. A glass card on a flat black background has no effect.
2. **Blur scales with elevation** — higher layers get more blur
3. **Inset highlight** — always include `inset 0 1px 0` top edge highlight for realism
4. **Border opacity scales with elevation** — more elevated = slightly more visible border
5. **Saturate with blur** — always pair `backdrop-filter: blur()` with `saturate(160–220%)`

---

## 5. Background System

Glass needs something to blur against. The background is a first-class design element.

### Primary Background Recipe

```css
body {
  background-color: var(--bg-base);
  background-image:
    radial-gradient(ellipse 80% 50% at 20% 10%, rgba(255,255,255,0.03) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 80%, rgba(255,255,255,0.02) 0%, transparent 60%),
    url("data:image/svg+xml,..."); /* Optional noise texture */
  min-height: 100vh;
}
```

### Background Noise Texture (Optional)

Add grain for depth. Use at 2–4% opacity over the base background:

```css
.bg-noise::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: url('/assets/noise.png'); /* 200×200 PNG noise tile */
  opacity: 0.03;
  pointer-events: none;
  z-index: 0;
}
```

### Ambient Glow Orbs

Large, blurred gradient orbs behind the main content create depth for glass to blur against:

```css
/* Usage: Place these as fixed pseudo-elements or absolute divs */
.orb-1 {
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(255,255,255,0.04) 0%, transparent 70%);
  border-radius: 50%;
  filter: blur(60px);
  position: fixed; top: -100px; left: -200px;
  pointer-events: none;
}

.orb-2 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, rgba(255,255,255,0.03) 0%, transparent 70%);
  border-radius: 50%;
  filter: blur(80px);
  position: fixed; bottom: -50px; right: -100px;
  pointer-events: none;
}
```

---

## 6. Spacing & Layout

8-point grid system. All spacing values are multiples of 4px.

```css
--space-1:  4px;
--space-2:  8px;
--space-3:  12px;
--space-4:  16px;
--space-5:  20px;
--space-6:  24px;
--space-8:  32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
--space-20: 80px;
--space-24: 96px;
```

### Dashboard Layout Grid

```
Sidebar:        240px fixed (collapsible to 64px)
Main content:   fluid, max-width 1400px
Content gutter: 24px (--space-6) on all sides
Card gap:       16px (--space-4)
Section gap:    32px (--space-8)
```

---

## 7. Border Radius

```css
--radius-sm:   4px;   /* Badges, tags, small chips */
--radius-md:   8px;   /* Buttons, inputs, small cards */
--radius-lg:   12px;  /* Standard cards, panels */
--radius-xl:   16px;  /* Larger cards, sidebars */
--radius-2xl:  20px;  /* Modals, sheets */
--radius-3xl:  28px;  /* Hero cards, feature panels */
--radius-full: 9999px; /* Pills, avatars, toggles */
```

---

## 8. Component Specs

### 8.1 Cards

```
Default Card:
  Background:     --glass-surface
  Border:         1px solid --border-default
  Border Radius:  --radius-lg
  Padding:        --space-6
  Blur:           12px

Stat Card (KPI):
  Same as default + top edge accent line
  border-top: 1px solid rgba(255,255,255,0.18)

Interactive Card:
  Hover: background → --glass-surface-hover, border → --border-strong
  Transition: all 200ms ease
```

### 8.2 Buttons

```
Primary Button:
  Background:     #ffffff
  Color:          #09090b  (--text-inverse)
  Border:         none
  Border Radius:  --radius-md
  Padding:        10px 20px
  Font:           14px, weight 500
  Hover:          background rgba(255,255,255,0.88), transform translateY(-1px)
  Active:         transform translateY(0)

Secondary Button:
  Background:     --glass-surface
  Border:         1px solid --border-default
  Color:          --text-primary
  Hover:          background --glass-surface-hover, border --border-strong

Ghost Button:
  Background:     transparent
  Border:         none
  Color:          --text-secondary
  Hover:          color --text-primary, background rgba(255,255,255,0.04)

Destructive Button:
  Background:     rgba(239, 68, 68, 0.12)
  Border:         1px solid rgba(239, 68, 68, 0.20)
  Color:          #fca5a5
```

### 8.3 Inputs

```
Text Input:
  Background:     rgba(255, 255, 255, 0.04)
  Border:         1px solid --border-input
  Border Radius:  --radius-md
  Padding:        10px 14px
  Font:           14px, --text-primary
  Placeholder:    --text-tertiary

  Focus:
    border-color: rgba(255,255,255,0.30)
    box-shadow: 0 0 0 3px rgba(255,255,255,0.06)
    outline: none

  Error:
    border-color: rgba(252, 165, 165, 0.40)
    box-shadow: 0 0 0 3px rgba(252, 165, 165, 0.08)
```

### 8.4 Navigation / Sidebar

```
Sidebar Container:
  Width:          240px
  Background:     rgba(255,255,255,0.03)
  Border-right:   1px solid --border-dim
  Padding:        --space-4

Nav Item:
  Padding:        8px 12px
  Border Radius:  --radius-md
  Color:          --text-secondary
  Font:           14px, weight 400

Nav Item (Active):
  Background:     rgba(255,255,255,0.07)
  Border:         1px solid rgba(255,255,255,0.08)
  Color:          --text-primary
  Font-weight:    500

Nav Item (Hover):
  Background:     rgba(255,255,255,0.04)
  Color:          --text-primary
```

### 8.5 Badges & Tags

```
Default Badge:
  Background:     rgba(255,255,255,0.06)
  Border:         1px solid rgba(255,255,255,0.10)
  Color:          --text-secondary
  Border Radius:  --radius-full
  Padding:        2px 10px
  Font:           11px, weight 500, uppercase, letter-spacing 0.06em

Status Badges: use --status-* tokens for background and text color
```

### 8.6 Data Tables

```
Table Container:
  Glass card wrapper (--glass-surface, border, blur)

Header Row:
  Background:     rgba(255,255,255,0.03)
  Border-bottom:  1px solid --border-dim
  Font:           11px, weight 500, uppercase, --text-tertiary, letter-spacing 0.08em

Data Row:
  Border-bottom:  1px solid --border-dim
  Padding:        12px 16px
  Font:           13px, --text-secondary

Row Hover:
  Background:     rgba(255,255,255,0.02)
  Color:          --text-primary
```

### 8.7 Tooltips

```
Background:     rgba(24, 24, 27, 0.92)
Border:         1px solid --border-strong
Border Radius:  --radius-md
Padding:        6px 10px
Font:           12px, --text-primary
Blur:           20px
Box Shadow:     0 8px 24px rgba(0,0,0,0.40)
```

### 8.8 Toasts / Notifications

```
Background:     rgba(255,255,255,0.06)
Border:         1px solid --border-strong
Border Radius:  --radius-lg
Padding:        12px 16px
Blur:           28px
Box Shadow:     0 16px 40px rgba(0,0,0,0.40)
Max Width:      360px
Position:       Fixed, bottom-right, --space-6 from edges
```

---

## 9. Motion & Transitions

```css
/* Timing functions */
--ease-out:     cubic-bezier(0.16, 1, 0.3, 1);   /* Snappy exits */
--ease-in-out:  cubic-bezier(0.4, 0, 0.2, 1);    /* Balanced */
--ease-spring:  cubic-bezier(0.34, 1.56, 0.64, 1); /* Gentle spring */

/* Durations */
--duration-fast:   120ms;   /* Micro-interactions (hover color) */
--duration-base:   200ms;   /* Buttons, inputs */
--duration-slow:   300ms;   /* Cards, panels */
--duration-slower: 500ms;   /* Page transitions, modals */
```

### Standard Transitions

```css
/* Interactive elements */
transition: background var(--duration-base) var(--ease-out),
            border-color var(--duration-base) var(--ease-out),
            box-shadow var(--duration-base) var(--ease-out),
            transform var(--duration-base) var(--ease-out);

/* Modal / overlay entrance */
@keyframes glass-enter {
  from { opacity: 0; transform: translateY(8px) scale(0.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
animation: glass-enter var(--duration-slower) var(--ease-spring);

/* Toast entrance */
@keyframes toast-in {
  from { opacity: 0; transform: translateX(20px); }
  to   { opacity: 1; transform: translateX(0); }
}
```

### Motion Rules

- Never animate `backdrop-filter` — it causes jank
- Animate `opacity` + `transform` only for performance
- Use `will-change: transform` sparingly and only on actively animating elements
- Respect `prefers-reduced-motion`:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 10. Iconography

- **Library:** [Lucide](https://lucide.dev) — consistent stroke-based icons
- **Default size:** 16px (nav), 18px (cards), 20px (headings)
- **Stroke width:** 1.5px
- **Color:** Inherit from text color token of context
- **Never fill icons** — stroke-only maintains the light, airy aesthetic

---

## 11. Shadow System

```css
--shadow-sm:
  0 1px 2px rgba(0, 0, 0, 0.20);

--shadow-md:
  0 1px 1px rgba(0, 0, 0, 0.12),
  0 4px 8px rgba(0, 0, 0, 0.24);

--shadow-lg:
  0 2px 4px rgba(0, 0, 0, 0.20),
  0 8px 20px rgba(0, 0, 0, 0.30);

--shadow-xl:
  0 4px 8px rgba(0, 0, 0, 0.30),
  0 16px 40px rgba(0, 0, 0, 0.40);

--shadow-2xl:
  0 8px 16px rgba(0, 0, 0, 0.35),
  0 32px 64px rgba(0, 0, 0, 0.45);

/* Glass inner highlight — always combine with outer shadow */
--shadow-inset-highlight:
  inset 0 1px 0 rgba(255, 255, 255, 0.08);
```

---

## 12. CSS Variables — Full Reference

```css
:root {
  /* Backgrounds */
  --bg-base:    #0a0a0b;
  --bg-subtle:  #111113;
  --bg-muted:   #18181b;

  /* Glass */
  --glass-surface:        rgba(255, 255, 255, 0.04);
  --glass-surface-hover:  rgba(255, 255, 255, 0.07);
  --glass-surface-active: rgba(255, 255, 255, 0.10);
  --glass-elevated:       rgba(255, 255, 255, 0.08);
  --glass-overlay:        rgba(0, 0, 0, 0.50);

  /* Borders */
  --border-dim:     rgba(255, 255, 255, 0.05);
  --border-default: rgba(255, 255, 255, 0.10);
  --border-strong:  rgba(255, 255, 255, 0.18);
  --border-input:   rgba(255, 255, 255, 0.12);

  /* Text */
  --text-primary:   #f4f4f5;
  --text-secondary: #a1a1aa;
  --text-tertiary:  #71717a;
  --text-disabled:  #3f3f46;
  --text-inverse:   #09090b;

  /* Accent */
  --accent-white:  #ffffff;
  --accent-silver: #d4d4d8;
  --accent-zinc:   #52525b;

  /* Status */
  --status-success:      rgba(134, 239, 172, 0.15);
  --status-success-text: #86efac;
  --status-warning:      rgba(253, 224, 71, 0.15);
  --status-warning-text: #fde047;
  --status-error:        rgba(252, 165, 165, 0.15);
  --status-error-text:   #fca5a5;
  --status-info:         rgba(147, 197, 253, 0.15);
  --status-info-text:    #93c5fd;

  /* Typography */
  --font-sans: 'DM Sans', sans-serif;
  --font-mono: 'DM Mono', monospace;

  /* Spacing */
  --space-1: 4px;   --space-2: 8px;   --space-3: 12px;
  --space-4: 16px;  --space-5: 20px;  --space-6: 24px;
  --space-8: 32px;  --space-10: 40px; --space-12: 48px;
  --space-16: 64px; --space-20: 80px; --space-24: 96px;

  /* Radii */
  --radius-sm:   4px;    --radius-md:   8px;
  --radius-lg:   12px;   --radius-xl:   16px;
  --radius-2xl:  20px;   --radius-3xl:  28px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm:  0 1px 2px rgba(0,0,0,0.20);
  --shadow-md:  0 1px 1px rgba(0,0,0,0.12), 0 4px 8px rgba(0,0,0,0.24);
  --shadow-lg:  0 2px 4px rgba(0,0,0,0.20), 0 8px 20px rgba(0,0,0,0.30);
  --shadow-xl:  0 4px 8px rgba(0,0,0,0.30), 0 16px 40px rgba(0,0,0,0.40);
  --shadow-2xl: 0 8px 16px rgba(0,0,0,0.35), 0 32px 64px rgba(0,0,0,0.45);
  --shadow-inset-highlight: inset 0 1px 0 rgba(255,255,255,0.08);

  /* Motion */
  --ease-out:    cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --duration-fast:   120ms;
  --duration-base:   200ms;
  --duration-slow:   300ms;
  --duration-slower: 500ms;
}
```

---

## 13. Do's and Don'ts

### ✅ Do

- Always place glass elements over a textured or gradient background
- Use `backdrop-filter` + `saturate()` together
- Add an inset top-edge highlight to every glass card
- Scale blur with elevation (more blur = higher layer)
- Keep palette disciplined — resist adding color beyond the system
- Use `DM Mono` for all numerical/data values in KPI cards

### ❌ Don't

- Don't place glass on a flat, featureless background
- Don't animate `backdrop-filter` (performance cost)
- Don't use more than 3 glass layers visible at once
- Don't make glass too opaque (over `0.15`) — it loses the effect
- Don't use colored glow orbs — this is a monochrome system
- Don't mix border-radius values arbitrarily — always use system tokens

---

*Design system version 1.0 — Monochrome Glassmorphism SaaS*
