#!/usr/bin/env python3
"""Validate the portable repository, not personal skill installation state."""
from pathlib import Path
import argparse, ast, hashlib, json, re, sys
from urllib.parse import unquote

def validate(root):
    root=root.resolve();fail=[];warn=[];checks={}
    skill=root/'skills/write-innovation-essays/SKILL.md'
    try:
        import yaml
        raw=skill.read_text(encoding="utf-8");parts=raw.split('---',2);front=yaml.safe_load(parts[1]);body=parts[2]
        if set(front)!={'name','description'}:fail.append('Skill metadata must contain only name and description in this portable edition.')
        if front.get('name')!=skill.parent.name:fail.append('Skill directory/name mismatch.')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',front.get('name','')):fail.append('Invalid skill name.')
        if not 1<=len(front.get('description',''))<=1024:fail.append('Invalid skill description length.')
        if len(raw.splitlines())>=500:fail.append('Skill entry is too long; move detail to deep references.')
        checks['skill_lines']=len(raw.splitlines());checks['skill_frontmatter']='valid'
    except (OSError,ValueError,IndexError,ImportError)as e:fail.append(f'Skill validation failed: {e}')
    required=['AGENTS.md','README.md','library/source-manifest.json','library/catalog.md','library/reading-routes.md','docs/chart-gallery.md','docs/document-schema.md','skills/write-innovation-essays/references/innovation-essay-hub-v5.md']
    for name in required:
        if not(root/name).is_file():fail.append(f'Missing required file: {name}')
    # Only active instructions/catalogs are link-checked. Historical manuscripts
    # contain old workspace links and are preserved as source records, not API docs.
    active=[root/'AGENTS.md',root/'README.md',skill,*root.glob('docs/*.md'),*root.glob('skills/write-innovation-essays/references/*.md'),*root.glob('library/*.md'),*root.glob('library/lessons/*.md'),*root.glob('cases/*/README.md')]
    link_count=0
    pattern=re.compile(r'!?\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))(?:\s+"[^"]*")?\)')
    for path in active:
        if not path.exists():continue
        # The original V5 contains illustrative template links, not all intended
        # as active files of this toolkit. Its exact-byte checksum controls it.
        if path.name=='innovation-essay-hub-v5.md':continue
        text=path.read_text(encoding="utf-8");text=re.sub(r'(?ms)^`{3,}.*?^`{3,}\s*$','',text)
        for m in pattern.finditer(text):
            target=(m.group(1)or m.group(2)).split('#',1)[0]
            if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target):continue
            target=unquote(target.replace('\\(','(').replace('\\)',')'));dest=(path.parent/target).resolve();link_count+=1
            if not dest.is_relative_to(root):fail.append(f'Link leaves repository: {path.relative_to(root)} → {target}')
            else:
                try:exists=dest.exists()
                except OSError:exists=False
                if not exists:fail.append(f'Broken local link: {path.relative_to(root)} → {target}')
    checks['local_links_checked']=link_count
    v5=root/'skills/write-innovation-essays/references/innovation-essay-hub-v5.md'
    if v5.exists():
        if hashlib.sha256(v5.read_bytes()).hexdigest()!='eed46f6bee81ed206c500f78a54ff5b7926d2dc7be325d57b41f62d60c7e18ff':fail.append('V5 differs from the supplied exact source.')
        else:checks['original_v5_sha256']='matches'
    manifest=root/'library/source-manifest.json';n=0
    if manifest.exists():
        data=json.loads(manifest.read_text(encoding="utf-8"));files=data.get('files',data if isinstance(data,list)else[])
        for item in files:
            rel=item.get('path',item.get('relative_path'));p=(root/rel).resolve()if rel else None
            if not p or not p.is_relative_to(root)or not p.is_file():fail.append(f'Missing/source path invalid: {rel}');continue
            if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:fail.append(f'Source changed: {rel}')
            n+=1
    checks['source_files_checked']=n
    syntax=0
    for p in [root/'studio.py',*root.glob('skills/write-innovation-essays/scripts/*.py'),*root.glob('tests/*.py')]:
        try:ast.parse(p.read_text(encoding="utf-8"),filename=str(p));syntax+=1
        except SyntaxError as e:fail.append(f'Python syntax error: {p.relative_to(root)}: {e}')
    checks['python_files_parsed']=syntax
    names={};big=[]
    for p in root.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(root).as_posix()
        if p.is_symlink():fail.append(f'Unexpected symlink: {rel}')
        key=rel.casefold()
        if key in names:fail.append(f'Case-insensitive path collision: {rel} and {names[key]}')
        names[key]=rel
        if any(x in {'.git','.venv','node_modules'}for x in p.relative_to(root).parts):fail.append(f'Unwanted dependency/history tree: {rel}')
        if p.name=='.env' or(p.name.startswith('.env.')and p.name!='.env.example'):fail.append(f'Environment file must not be packaged: {rel}')
        if any(re.search(r'[<>:"|?*]',part)or part.endswith((' ','.'))for part in p.relative_to(root).parts):fail.append(f'Windows-unsafe archive path: {rel}')
        if p.stat().st_size>=100*1024**2:big.append({'path':rel,'bytes':p.stat().st_size})
    if big:warn.append({'message':'Files >=100 MiB may need large-file storage on some repository hosts.','files':big})
    checks['repository_files']=len(names)
    return {'status':'pass'if not fail else'fail','checks':checks,'failures':fail,'warnings':warn,'scope':'Structure, links, supplied-file hashes, syntax and portable paths. Functional tools and actual visual QA require their separate recorded tests. No installed-skill claim.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path,nargs='?',default=Path(__file__).resolve().parents[3]);p.add_argument('--output',type=Path);a=p.parse_args();r=validate(a.root)
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n', encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2));sys.exit(0 if r['status']=='pass'else 1)
