---
name: frontend-preview
description: Open a browser to preview frontend pages during development, screenshot the page, analyze it with AI vision, and automatically fix visual issues in a feedback loop. Use this skill whenever you're writing or modifying HTML/CSS/JSX/TSX/Vue/Svelte files, building UI components or pages, working on styling or layout, or the user mentions previewing, checking the page, seeing the result, or opening a browser. Also use when the user says "预览", "打开浏览器", "看看效果", or any phrase about checking how something looks.
---

# Frontend Preview - Browser Preview + AI Visual Review

When building frontend UI, use this skill to open the page in a real browser, capture a screenshot, and let AI vision analyze the rendering. If issues are found, fix the code and repeat until the page looks correct.

**This skill is for the main conversation agent.** You determine the preview URL, open the browser, capture the screenshot, analyze it, and iterate on fixes. **Execute each step directly — run the actual commands, open the real browser, take the real screenshot. Do NOT describe what you "would" do.**

## When to use this skill

Use proactively when:
- You've just written or modified frontend code (HTML, CSS, React/Vue/Svelte components, layout, styling)
- The user asks to see the result ("预览一下", "打开看看", "what does this look like?", "check the page")
- You're uncertain about whether your CSS/styling changes will render correctly

Skip when:
- Changes are pure logic/backend (API handlers, database queries, CLI tools)
- No dev server is running and none can be started (e.g., static HTML without a server — in that case, just `open file.html` directly)
- The page requires authentication that isn't configured

## Workflow

### Step 1: Determine the preview URL

Try in order:

1. **Check project config files** — read one of these for the dev server port:
   - `vite.config.js/ts` → `server.port` (default 5173)
   - `package.json` → `scripts.dev` often reveals the command and port
   - `next.config.js/ts` → default 3000
   - `webpack.config.js` → `devServer.port`
   - `angular.json` → `serve.options.port` (default 4200)
   - `.env` / `.env.local` → `PORT`, `VITE_PORT`, `DEV_PORT`

2. **Scan for running dev servers** — check common ports with `lsof`:
   ```bash
   lsof -iTCP -sTCP:LISTEN -P -n 2>/dev/null | grep -E ':(3000|5173|8080|4200|8000|5000|3001|6006|1420|1234|4444|9090)\b'
   ```

3. **Build the URL**: combine host (default `localhost`) with the detected port.

If no dev server is found, proceed to Step 1b.

### Step 1b: Start a dev server if needed

If no server is running, start one. Check `package.json` scripts and pick the first match:
```bash
npm run dev 2>&1 &
# or: npm start, npm run serve, npx vite, npx next dev, etc.
```

Wait for the server to be ready (poll the port until it responds):
```bash
for i in $(seq 1 30); do curl -s -o /dev/null "http://localhost:<PORT>" && break; sleep 1; done
```

Then go back to Step 1 to confirm the URL.

### Step 2: Open the browser

Use `open` with the URL. This opens the user's default browser:

```bash
open "http://localhost:<PORT><PATH>"
```

The path defaults to `/` but can be a specific route (e.g., `/dashboard`, `/profile`) if the user mentioned one.

If the user has a preference for a specific browser, use `open -a "Google Chrome"` or `open -a "Firefox"` instead.

### Step 3: Wait for the page to render

Give the browser time to load and render the page:

```bash
sleep 3
```

For pages with heavy JS or async data, wait longer (5-8 seconds).

### Step 4: Capture a screenshot

Use `screencapture` to capture the screen. Since the browser was just opened, it should be the frontmost window:

```bash
screencapture -x -T 0 /tmp/frontend-preview.png
```

- `-x`: no sound
- `-T 0`: no delay (page already loaded from the sleep in Step 3)

For a more targeted capture of just the browser window, use AppleScript to capture the frontmost window:

```bash
osascript -e '
tell application "System Events"
  set frontApp to name of first application process whose frontmost is true
  set windowID to id of window 1 of application process frontApp
end tell
' 2>/dev/null
```

Then: `screencapture -x -l <windowID> /tmp/frontend-preview.png`

### Step 5: Analyze the screenshot with AI vision

Use `mcp__MiniMax__understand_image` to analyze the screenshot. Provide context about what the page should look like:

```
Analyze this screenshot of a frontend page. The expected design is:
[DESCRIBE what you intended to build — layout, colors, elements, interactions]

Check for:
1. Layout issues — misaligned elements, overflow, broken grids, unexpected wrapping
2. Styling issues — wrong colors, missing backgrounds, incorrect fonts, spacing problems
3. Content issues — missing text, truncated content, overlapping elements, incorrect rendering
4. Responsive issues — elements that look wrong at this viewport width
5. Functional issues — buttons that look disabled, missing icons, broken images

For each issue found, state:
- What the problem is (be specific)
- Where it is on the page
- The likely CSS/HTML cause
- How to fix it
```

### Step 6: Fix issues and iterate

If the analysis found issues:
1. Apply the fixes to the code
2. Refresh the browser: `open "http://localhost:<PORT><PATH>"` (opens a new tab) or use AppleScript to reload
3. Wait for render: `sleep 2`
4. Re-capture screenshot and re-analyze

Stop after 3 iterations. If issues persist, report them to the user with the screenshots and your analysis. Some issues (sub-pixel rendering, font differences) may be inherent to the OS/browser and not fixable in code.

### Step 7: Report to the user

Summarize what you did:
- URL opened
- Screenshot location: `/tmp/frontend-preview.png`
- Issues found and fixed
- Remaining issues (if any)

The user can view the latest screenshot at `/tmp/frontend-preview.png`.

## Edge cases

### Port already in use
If the expected port is taken, scan for the actual port with `lsof` (Step 1). Use whatever is actually listening.

### Multiple dev servers
If multiple frontend ports are detected, prefer: Vite (5173) > Next.js (3000) > Create React App (3000) > Vue CLI (8080) > Angular (4200). If ambiguous, ask the user which one to preview.

### Dev server fails to start
Check for common issues:
- Missing `node_modules`: run `npm install`
- Port conflict: kill the existing process or use a different port
- Missing env vars: check `.env.example` vs `.env`
If it still fails, tell the user and suggest they start the server manually.

### Page is blank or shows an error
This is a valid finding. The AI analysis will detect blank pages, error overlays, or build error screens. Treat these as critical issues to fix immediately.

### Hot reload already running
If the dev server supports HMR (Vite, Next.js, etc.), code changes may already be reflected. You can skip opening a new tab and just capture the screenshot after making changes — the page should auto-update.

### Static HTML files
For plain `.html` files without a server, open directly:
```bash
open /path/to/file.html
```
Then screenshot as normal. No port scanning needed.
