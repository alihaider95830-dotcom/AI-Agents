# Studio Frontend Visual Improvements Prompt

You are tasked with improving the visual design of the Studio landing page. Make the following three CSS and styling changes to enhance visual hierarchy, clarity, and user engagement.

## 1. Add a Visual Badge/Pill for the Free Offer

**Current state:** The text "Free forever · No credit card required · 2 reports per month" appears as plain paragraph text below the CTA buttons.

**Desired change:**
- Wrap this text in a styled badge or pill container
- Apply a bordered background with a subtle color (light green, blue, or accent color matching your brand)
- Use a semi-transparent background (e.g., rgba with 10-15% opacity) or solid light tint
- Add a thin border in the accent color
- Increase font size slightly (14px → 15-16px)
- Add horizontal padding (16-20px) and vertical padding (8-12px)
- Center it below the buttons
- Make the text color darker for better contrast
- Optional: Add a small icon (star, check, or lock icon) before the text for visual interest

**Goal:** The free offer becomes visually prominent and catches the eye immediately, increasing conversion potential.

---

## 2. Strengthen CTA Button Hierarchy

**Current state:** "Generate your first report" and "See a sample report" buttons appear similar in visual weight.

**Desired change:**
- **Primary button ("Generate your first report"):**
  - Use a solid, bold accent color (blue, brand primary, or gradient)
  - Increase padding (16px vertical × 24px horizontal minimum)
  - Add subtle shadow (e.g., `box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15)`)
  - White or light text color for contrast
  - Hover effect: slightly darker shade or shadow lift
  - Optional: Add a subtle scale or lift animation on hover

- **Secondary button ("See a sample report"):**
  - Use an outline or ghost style (transparent background, colored border)
  - Lighter color (gray-500 or secondary color)
  - Same padding as primary for consistency
  - Hover effect: light background fill or border color intensify

**Goal:** Users immediately understand which action is the primary conversion goal.

---

## 3. Add Visual Separators & Better Section Spacing

**Current state:** Major sections (hero, performance metrics, pipeline, features) blend together with minimal visual separation.

**Desired change:**
- Add subtle horizontal dividers between major sections:
  - Use a thin line (1px solid in rgba(0, 0, 0, 0.1) or light gray)
  - OR use increased spacing (48-64px margin-top/bottom)
  
- Increase vertical padding on sections:
  - Hero section: 80-100px top and bottom
  - Other sections: 60-80px top and bottom
  
- Optional: Add alternating background colors:
  - Hero: white/default
  - Performance metrics: light gray (e.g., #f9fafb or #f3f4f6)
  - Pipeline: white/default
  - Features: light gray
  - This creates visual rhythm without being harsh

- Ensure consistent spacing around card groups (e.g., the 4 agent cards, the 4 feature cards)

**Goal:** The page feels more organized, easier to scan, and content flows naturally with clear section boundaries.

---

## Implementation Notes

- Use Tailwind CSS utility classes where possible (e.g., `bg-blue-50`, `border-blue-200`, `shadow-md`)
- Ensure responsive design: spacing and sizing should adapt to mobile (reduce padding, smaller badges on small screens)
- Test hover states and transitions across all buttons
- Keep the overall design consistent with the existing color palette and typography
- All changes should be visual only—no new components, no logic changes, no new pages

---

## Files to Update

- [src/app/page.tsx](src/app/page.tsx) (main landing page component)
- Check [tailwind.config.ts](tailwind.config.ts) for any custom color/spacing overrides needed

