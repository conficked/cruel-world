# Cruel World — closed alpha

A keyboard-only, three-hero campaign across four realms. This alpha is for playtesting; balance, performance, and presentation may change.

Live browser build: https://conficked.github.io/cruel-world/

Click the launch screen, then click the game to focus it. Use arrows/WASD and Enter/Space in menus. Move with A/D or Left/Right; Space jumps; W/S or Up/Down climbs; F attacks; E uses the class ability; Shift or Q uses class-specific defensive mobility. Escape/P pauses; losing focus also pauses. Sound and volume are in Settings. Use the host fullscreen button in the browser.

Browser high scores, selected hero, settings, and furthest region are session-only. Reloading or closing the page loses them; this is not a resumable campaign save. Desktop saves retain their normal behavior. Audio needs a launch click and may be muted by browser policy. Keyboard required; touch controls and mobile play are not supported. First launch downloads the pygbag Python/Pygame runtime from its CDN, so an internet connection is required. Browser performance and audio may differ from desktop. Quit ends the game; reload to launch again.

Feedback: Which hero and browser/OS did you use? Were controls and objectives clear? Where did difficulty spike? Did audio, focus/pause, or performance fail? For bugs, include realm, wave, hero, and steps to reproduce.

Build: `.venv/bin/pip install -r requirements-web.txt`, then `.venv/bin/python build_web.py`. FFmpeg with libvorbis must be installed; only staged WAV copies are converted to OGG. Output: `dist/cruel-world-closed-alpha.zip`. The build stages runtime modules, derived hero sprites, required scenery, fonts, audio, and license records; source packs, tests, caches, and development artifacts are excluded.

On itch.io choose HTML Game, upload the ZIP and mark it playable in browser. Use an 800×600 embed, Click to Play, and the fullscreen button; leave Mobile Friendly disabled. Keep the project restricted for the closed alpha and preview the uploaded game before inviting testers. No itch.io upload or publication is performed by the build.
