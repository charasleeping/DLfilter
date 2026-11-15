"""Build a platform source/native ZIP from a committed release and a compiled executable."""
import argparse
import io
import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import tempfile
import zipfile


def main():
    p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--output',type=Path,default=Path('dist'));p.add_argument('--working-tree',action='store_true',help='Package current application files for local review instead of committed HEAD');args=p.parse_args()
    machine=platform.machine().lower();machine={'amd64':'x86_64','aarch64':'arm64'}.get(machine,machine)
    name=f'DLfilter-{args.tag}-{platform.system().lower()}-{machine}'
    args.output.mkdir(parents=True,exist_ok=True)
    executable='dlfilter.exe' if os.name=='nt' else 'dlfilter'
    binary=Path('target/release')/executable
    helper=Path('dist')/('dlfilter-titles.exe' if os.name=='nt' else 'dlfilter-titles')
    if not helper.is_file(): raise SystemExit('Build the bundled title helper before packaging')
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)/name;root.mkdir()
        if args.working_tree:
            # Explicit allowlist avoids including personal data or build caches.
            for folder_name in ('src','module','static','templates','docs'):
                shutil.copytree(folder_name,root/folder_name,ignore=shutil.ignore_patterns('__pycache__'))
            for pattern in ('README*.md','LICENSE','Cargo.*','app.py','initial.py','start.*','compose.yaml','Dockerfile','pyproject.toml','uv.lock','requirements.txt','recover_works_table_download.py'):
                for source in Path('.').glob(pattern):
                    if source.is_file(): shutil.copyfile(source,root/source.name)
        else:
            archive=subprocess.check_output(['git','archive','--format=tar','HEAD'])
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                tar.extractall(root,filter='data')
        (root/'bin').mkdir(exist_ok=True);(root/'bin'/executable).write_bytes(binary.read_bytes())
        (root/'bin'/helper.name).write_bytes(helper.read_bytes())
        bat=root/'start.bat';bat.write_bytes(bat.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
        with zipfile.ZipFile(args.output/(name+'.zip'),'w',zipfile.ZIP_DEFLATED) as z:
            for file in root.rglob('*'):
                if file.is_file():
                    info=zipfile.ZipInfo(str(file.relative_to(root.parent)).replace('\\','/'));info.create_system=3
                    info.external_attr=(0o100755 if file.name in ('dlfilter','dlfilter-titles','start.command') else 0o100644)<<16
                    z.writestr(info,file.read_bytes(),compress_type=zipfile.ZIP_DEFLATED)
        output=args.output/(name+'.zip')
        with output.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
        output.with_suffix('.zip.sha256').write_text(f'{digest}  {output.name}\n')
        print(output)

if __name__=='__main__':main()
