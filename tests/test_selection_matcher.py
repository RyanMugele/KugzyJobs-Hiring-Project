"""Worked scoring examples and the creator's applicant selection workflow."""
import pytest
from flask import template_rendered
from test_workflows import app, login, post, job
from app import db
from app.models.user import User
from app.models import Editor, Portfolio, Job, JobApplication
from app.nlp.editor_matcher import calculate_match_score
from app.nlp.job_parser import parse_job_description

REQUIRED = {'skills':['Adobe Premiere Pro','Color Grading'],'styles':['cinematic'],'niches':['travel']}

@pytest.mark.parametrize('requirements,offered,expected', [
 (REQUIRED, REQUIRED, 100),
 (REQUIRED, {'skills':['Adobe Premiere Pro'],'styles':['cinematic'],'niches':['travel']},75),
 (REQUIRED, {'skills':['Adobe Premiere Pro','Color Grading']},50),
 (REQUIRED, {'skills':['CapCut'],'styles':['fast-paced'],'niches':['gaming']},0),
 ({'skills':['Adobe Premiere Pro','Color Grading']},{'skills':['Adobe Premiere Pro']},50),
 ({},{'skills':['Adobe Premiere Pro']},0),
 ({'skills':['Adobe Premiere Pro','Adobe Premiere Pro']},{'skills':' ADOBE PREMIERE PRO ; Adobe Premiere Pro '},100),
])
def test_score_examples(requirements,offered,expected):
 assert calculate_match_score(requirements,offered)==expected


def candidates(app):
 j=job(app)
 with app.app_context():
  item=db.session.get(Job,j)
  item.updateJobDetails(description='Cinematic travel editing in Premiere Pro with color grading')
  assert parse_job_description(item.description)==REQUIRED
  first=db.session.get(Editor,1);first.specializations='Adobe Premiere Pro'
  u=User(fullName='Second Editor',emailAddress='second@example.com',userType='editor',password='Testing12345!')
  second=Editor(user=u,specializations='Adobe Premiere Pro, Color Grading')
  db.session.add(second);db.session.flush()
  for e in (first,second):
   db.session.add(Portfolio(editorId=e.editorId,title='Cinematic travel reel',description='Cinematic travel work',videoUrl='https://example.com/reel',skillTags='',verificationStatus='approved'))
   db.session.add(JobApplication(jobId=j,editorId=e.editorId,proposedRate=150,status='pending'))
  db.session.commit()
  return j,first.editorId,second.editorId


def context_for(client,path,app):
 captured=[]
 def capture(sender,template,context,**extra):captured.append(context)
 template_rendered.connect(capture,app)
 try:assert client.get(path).status_code==200
 finally:template_rendered.disconnect(capture,app)
 return captured[-1]


def test_ranked_applicants_and_creator_selects_lower_score(app):
 j,first,second=candidates(app);c=login(app,'creator')
 ctx=context_for(c,f'/creator/jobs/{j}/applications',app)
 assert [a.editorId for a in ctx['pending_applications']]==[second,first]
 assert sorted(ctx['application_match_scores'].values())==[75,100]
 with app.app_context():assert db.session.get(Job,j).selectedEditorId is None
 # Ranking assists the creator: a deliberate lower-scoring selection is allowed.
 assert post(c,f'/creator/jobs/{j}/select-editor',{'editorId':first},'/creator/profile').status_code==302
 with app.app_context():
  item=db.session.get(Job,j)
  assert item.selectedEditorId==first and item.status=='in_progress'
  assert {a.editorId:a.status for a in item.applications}=={first:'accepted',second:'declined'}
 # A repeated selection must not replace the assigned editor.
 post(c,f'/creator/jobs/{j}/select-editor',{'editorId':second},'/creator/profile')
 with app.app_context():assert db.session.get(Job,j).selectedEditorId==first


def test_pending_and_rejected_portfolios_do_not_raise_score(app):
 j,first,second=candidates(app);c=login(app,'creator')
 with app.app_context():
  for p in db.session.get(Editor,first).portfolios:p.verificationStatus='pending'
  for p in db.session.get(Editor,second).portfolios:p.verificationStatus='rejected'
  db.session.commit()
 ctx=context_for(c,f'/creator/jobs/{j}/applications',app)
 assert sorted(ctx['application_match_scores'].values())==[25,50]


def test_other_creator_cannot_select(app):
 j,first,second=candidates(app);c=login(app,'other')
 post(c,f'/creator/jobs/{j}/select-editor',{'editorId':first},'/creator/profile')
 with app.app_context():
  item=db.session.get(Job,j);assert item.status=='posted' and item.selectedEditorId is None
  assert all(a.status=='pending' for a in item.applications)


def test_nonapplicant_cannot_be_selected(app):
 j=job(app);c=login(app,'creator')
 post(c,f'/creator/jobs/{j}/select-editor',{'editorId':1},'/creator/profile')
 with app.app_context():
  item=db.session.get(Job,j);assert item.status=='posted' and item.selectedEditorId is None
