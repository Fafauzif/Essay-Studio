"""Exercise relocated entry point, safe paths and argument preservation."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]

class PortableCLI(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='essay studio ');self.repo=Path(self.temp.name)/'relocated';self.repo.mkdir();shutil.copyfile(ROOT/'studio.py',self.repo/'studio.py')
        self.scripts=self.repo/'skills/write-innovation-essays/scripts';self.scripts.mkdir(parents=True);shutil.copyfile(ROOT/'skills/write-innovation-essays/scripts/analysis.py',self.scripts/'analysis.py')
    def tearDown(self):self.temp.cleanup()
    def runcli(self,*args):return subprocess.run([sys.executable,str(self.repo/'studio.py'),*args],cwd=self.temp.name,text=True,capture_output=True)
    def test_project_is_relative_to_relocated_repo_not_cwd(self):
        r=self.runcli('new','course-packs','--language','en');self.assertEqual(r.returncode,0,r.stderr);record=self.repo/'projects/course-packs/project-record.json';self.assertEqual(json.loads(record.read_text())['language'],'en');r=self.runcli('new','course-packs');self.assertEqual(r.returncode,2);self.assertTrue(record.exists())
    def test_no_path_escape(self):
        self.assertEqual(self.runcli('new','../outside').returncode,2);self.assertFalse((self.repo.parent/'outside').exists())
    def test_analysis_arguments_with_spaces(self):
        inp=self.repo/'plan with spaces.json';out=self.repo/'result with spaces.json';inp.write_text(json.dumps({'months':3,'units':10,'unit_price':10,'unit_variable_cost':4,'fixed_cost':20,'setup_cost':100}))
        r=self.runcli('analyze','finance',str(inp),'--output',str(out));self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(out.read_text())['base']['npv'],20)
    def test_manifest_detects_changed_bytes(self):
        lib=self.repo/'library';lib.mkdir();raw=lib/'supplied.txt';raw.write_bytes(b'original supplied bytes');manifest={'files':[{'path':'library/supplied.txt','sha256':hashlib.sha256(raw.read_bytes()).hexdigest()}]};(lib/'source-manifest.json').write_text(json.dumps(manifest))
        self.assertEqual(self.runcli('verify-library').returncode,0);raw.write_bytes(b'changed');self.assertEqual(self.runcli('verify-library').returncode,1)
    def test_help_is_available_without_renderer(self):
        r=self.runcli('--help');self.assertEqual(r.returncode,0);self.assertIn('verify-library',r.stdout)
    def test_unicode_json_does_not_depend_on_locale_default(self):
        inp=self.repo/'unicode.json';out=self.repo/'unicode-result.json';value={'factors':[{'factor':'Akses café Δ','weight':1,'rating':4}]};inp.write_bytes(json.dumps(value,ensure_ascii=False).encode('utf-8'))
        env={**os.environ,'PYTHONUTF8':'0','LC_ALL':'C','PYTHONCOERCECLOCALE':'0'}
        r=subprocess.run([sys.executable,str(self.repo/'studio.py'),'analyze','score',str(inp),'--output',str(out)],cwd=self.temp.name,env=env,capture_output=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(out.read_bytes().decode('utf-8'))['factors'][0]['factor'],'Akses café Δ')

if __name__=='__main__':unittest.main()
