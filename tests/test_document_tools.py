"""Integration checks for document mechanics; no research/visual approval claim.

Run: python -m unittest discover -s tests -p 'test_document_tools.py' -v
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from docx import Document
from lxml import etree as ET

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skills/write-innovation-essays/scripts'
def load(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
build=load('build_docx');extract=load('extract_comments');audit=load('audit_document');render=load('render_document')

class DocumentMechanics(unittest.TestCase):
    def test_real_internal_links_without_self_linked_heading(self):
        p={'title':'Mechanics fixture','body':[{'type':'paragraph','text':'The calculation is in Appendix A.1.'}],'appendices':[{'id':'A.1','title':'Calculation','blocks':[]}]}
        with tempfile.TemporaryDirectory()as d:
            path=Path(d)/'fixture.docx';b=build.Builder(p,Path(d));build.save_docx(b.build(),path)
            r=audit.audit(path);self.assertEqual(r['errors'],[]);self.assertEqual(r['internal_links'],4)
            with zipfile.ZipFile(path)as z:
                x=ET.fromstring(z.read('word/document.xml'));ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                heads=x.xpath('//w:p[w:pPr/w:pStyle[starts-with(@w:val,"Heading")]]',namespaces=ns)
                self.assertFalse(any(h.xpath('.//w:hyperlink',namespaces=ns)for h in heads))

    def test_unknown_link_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unresolved'):
            build.Builder({'title':'Fixture','body':[{'text':'See Appendix Z.9.'}]},Path.cwd()).build()

    def test_table_cannot_overflow_text_region(self):
        with self.assertRaisesRegex(ValueError,'exceed'):
            build.Builder({'title':'Fixture','body':[{'type':'table','headers':['One','Two'],'rows':[['a','b']],'widths_cm':[12,12]}]},Path.cwd()).build()

    def test_comment_range_crosses_paragraphs_and_source_unchanged(self):
        with tempfile.TemporaryDirectory()as d:
            path=Path(d)/'review.docx';doc=Document();a=doc.add_paragraph().add_run('First selected paragraph');b=doc.add_paragraph().add_run('Second selected paragraph')
            doc.add_comment([a,b],text='Clarify this connection',author='Fixture reviewer');doc.save(path)
            before=hashlib.sha256(path.read_bytes()).hexdigest();result=extract.extract(path)
            self.assertEqual(result['comment_count'],1);self.assertEqual(result['comments'][0]['selection']['text'],'First selected paragraph\nSecond selected paragraph')
            self.assertEqual(before,hashlib.sha256(path.read_bytes()).hexdigest())

    def test_missing_converter_is_reported_as_failure(self):
        with tempfile.TemporaryDirectory()as d:
            path=Path(d)/'fixture.docx';build.save_docx(build.Builder({'title':'Fixture'},Path(d)).build(),path)
            r=render.render(path,Path(d)/'render',executable=str(Path(d)/'missing-converter'))
            self.assertEqual(r['status'],'failed');self.assertEqual(r['visual_review'],'not_performed_by_script')

    def test_neutral_template_has_no_author_or_comments(self):
        path=ROOT/'skills/write-innovation-essays/assets/templates/neutral_essay.docx'
        doc=Document(path);self.assertFalse(doc.core_properties.author);self.assertFalse(doc.core_properties.last_modified_by)
        r=audit.audit(path);self.assertEqual(r['comments'],0);self.assertEqual(r['tracked_changes'],0)

if __name__=='__main__':unittest.main()
