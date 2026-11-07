"""Stage runtime files and build a validated itch.io HTML5 archive."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
# pygbag's CDN no longer serves browserfs.min.js, so the loader template's script tag
# must resolve to a copy shipped inside the archive.
BROWSERFS = ROOT / 'assets/web/browserfs.min.js'
BROWSERFS_SHA256 = 'a2a2b38cd567dc20cd024e681df55f34f42174c692f553f8350dae171c2b875b'
MODULES = ('underworld_transitions.py', 'underworld.py', 'underworld_features.py', 'zerie_runtime.py', 'main.py', 'config.py', 'assets.py', 'audio.py', 'camera.py', 'campaign.py',
           'progression.py', 'camp.py', 'camp_interior.py', 'region_features.py', 'game_state.py', 'level.py', 'persistence.py', 'projectile.py', 'scenery.py', 'ui.py')


def runtime_files(root=ROOT):
    from assets import HERO_MANIFEST, MONSTER_MANIFEST, FOREST_ROOT, MOON_ROOT
    files = {root / name for name in MODULES}
    from campaign import ENVIRONMENTS
    # Required authored scores must fail staging loudly if a build omits them.
    for environment in ENVIRONMENTS:
        if 'boss_music' in environment:
            for key in ('music', 'boss_music'):
                path = root / 'assets/audio/tommusic/music' / (environment[key] + '.ogg')
                if not path.is_file():
                    raise FileNotFoundError(path)
                files.add(path)
    files.update((root / 'entities').glob('*.py'))
    from zerie_runtime import runtime_sources
    files.update(root / path.relative_to(ROOT) for path in runtime_sources(HERO_MANIFEST, MONSTER_MANIFEST))
    from underworld import runtime_sources as infernal_sources
    files.update(root / path.relative_to(ROOT) for path in infernal_sources())
    for species in MONSTER_MANIFEST:
        files.update((root / 'assets/enemies/luizmelo/Monsters_Creatures_Fantasy' / species).glob('*.png'))
    for name in ('Background/Background.png', 'Trees/Dark-Tree.png', 'Assets/Tiles.png',
                 'Assets/Interior-01.png', 'Assets/Buildings.png', 'Assets/Props-Rocks.png'):
        files.add(root / 'assets' / FOREST_ROOT / name)
    for name in ('Background_0.png', 'Background_1.png', 'Tiles.png'):
        files.add(root / 'assets' / MOON_ROOT / name)
    for directory in ('audio', 'fonts', 'licenses', 'ui', 'regions'):
        files.update(p for p in (root / 'assets' / directory).rglob('*')
                     if p.is_file() and p.suffix.lower() in ('.ogg', '.wav', '.ttf', '.txt', '.png', '.md'))
    return sorted(files)


def verify_browserfs():
    if not BROWSERFS.is_file():
        raise FileNotFoundError(BROWSERFS)
    digest = hashlib.sha256(BROWSERFS.read_bytes()).hexdigest()
    if digest != BROWSERFS_SHA256:
        raise ValueError(f'browserfs.min.js checksum mismatch: {digest}')


def validate_archive(path):
    with zipfile.ZipFile(path) as archive:
        files = [entry for entry in archive.infolist() if not entry.is_dir()]
        if 'index.html' not in archive.namelist() or archive.testzip():
            raise ValueError('Missing root index.html or corrupt ZIP')
        if 'browserfs.min.js' not in archive.namelist():
            raise ValueError('Missing vendored browserfs.min.js')
        index = archive.read('index.html').decode()
        if 'browserfs.min.js' not in index:
            raise ValueError('index.html does not load the vendored browserfs.min.js')
        if re.search(r'src="https?://[^"]*browserfs', index):
            raise ValueError('index.html still loads browserfs.min.js from a CDN')
        if len(files) > 1000 or sum(f.file_size for f in files) > 500_000_000:
            raise ValueError('Archive exceeds itch.io total limits')
        if any(f.file_size > 200_000_000 or len(f.filename) > 240 or
               f.filename.startswith('/') or '..' in Path(f.filename).parts for f in files):
            raise ValueError('Archive exceeds itch.io file limits or has unsafe paths')
        return {'files': len(files), 'bytes': path.stat().st_size,
                'extracted_bytes': sum(f.file_size for f in files)}


def polish_index(html):
    # pygbag's itch ZIP omits the tar used by its localhost branch.
    branch = "if platform.window.location.host.find('.itch.zone')>0:"
    if branch not in html:
        raise ValueError('pygbag loader template changed; review archive loading')
    html = html.replace(branch, 'if True:  # use the packaged ZIP on every host')
    html = html.replace('platform.document.body.style.background = "#7f7f7f"',
                        'platform.document.body.style.background = "#100e14"')
    # The vendored copy replaces the retired CDN script so the archive is self-contained.
    html, replaced = re.subn(r'src="[^"]*browserfs\.min\.js"', 'src="browserfs.min.js"', html)
    if replaced != 1:
        raise ValueError('pygbag template browserfs script tag changed; review archive loading')
    style = """<style>
body { background: #100e14; color: #e6dbb8; }
#infobox { background: #201a24; color: #e6dbb8; border: 1px solid #a6854c;
 font: 16px Georgia, serif; box-shadow: 0 8px 32px #0008; }
#status { color: #e6dbb8; }
#progress { accent-color: #a6854c; }
canvas { image-rendering: pixelated; }
</style>"""
    return html.replace('<body>', style + '\n<body>')


def main():
    verify_browserfs()
    output = ROOT / 'dist/cruel-world-closed-alpha.zip'
    output.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='cruelworld-web-') as temporary:
        stage = Path(temporary) / 'cruelworld'
        stage.mkdir()
        for source in runtime_files():
            target = stage / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.suffix == '.wav':
                subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(source),
                                '-c:a', 'libvorbis', str(target.with_suffix('.ogg'))], check=True)
            else:
                shutil.copy2(source, target)
        subprocess.run([sys.executable, '-m', 'pygbag', '--build', '--archive', '--no_opt',
                        '--title', 'Cruel World | Closed Alpha', '--app_name', 'Cruel World',
                        '--package', 'com.jupiternull.cruelworld', '--ume_block', '1', str(stage)], check=True)
        built = stage / 'build/web.zip'
        with zipfile.ZipFile(built) as source, zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as published:
            for name in source.namelist():
                data = source.read(name)
                if name == 'index.html':
                    data = polish_index(data.decode()).encode()
                published.writestr(name, data)
            published.write(BROWSERFS, 'browserfs.min.js')
            published.write(ROOT / 'PLAYTEST.md', 'PLAYTEST.md')
        result = validate_archive(output)
    print(json.dumps({'artifact': str(output), **result}, indent=2))


if __name__ == '__main__':
    main()
