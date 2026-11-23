import re
import pytest
from datetime import date,timedelta,datetime
from app import create_app,db
from app.models.user import User
from app.models import Creator,Editor,Admin,Job,Portfolio,JobApplication,Payment,Rating,Message,PasswordResetToken

@pytest.fixture
def app():
 app=create_app('testing')
 with app.app_context():
  db.create_all()
  for role,cls in [('creator',Creator),('editor',Editor),('admin',Admin),('other',Creator)]:
   u=User(fullName=role.title()+' Demo',emailAddress=role+'@example.com',userType='creator' if role=='other' else role,password='Testing12345!')
   db.session.add(u);db.session.flush();db.session.add(cls(userId=u.userId))
  db.session.commit()
 yield app
 with app.app_context():db.drop_all()

def token(client,path):
 res=client.get(path)
 match=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',res.text)
 assert match,(path,res.status_code)
 return match.group(1)

def post(client,path,data,token_path=None):
 data=dict(data);data['csrf_token']=token(client,token_path or path)
 return client.post(path,data=data)

def login(app,role):
 c=app.test_client()
 res=post(c,'/auth/login',dict(emailAddress=role+'@example.com',password='Testing12345!'))
 assert res.status_code==302
 return c

def job(app):
 with app.app_context():
  creator=User.query.filter_by(emailAddress='creator@example.com').first().creator
  j=creator.postJob(dict(title='Travel editing',description='Cinematic travel Premiere Pro',budgetMin=100,budgetMax=200,deadline=date.today()+timedelta(days=30)))
  return j.jobId

@pytest.mark.parametrize('role,path',[('creator','/creator/dashboard'),('creator','/creator/jobs'),('creator','/creator/editors'),('creator','/creator/analytics'),('creator','/creator/profile'),('editor','/editor/dashboard'),('editor','/editor/portfolio'),('editor','/editor/jobs'),('editor','/editor/applications'),('editor','/editor/profile'),('admin','/admin/dashboard'),('admin','/admin/users'),('admin','/admin/portfolios'),('admin','/admin/reports')])
def test_role_pages(app,role,path):
 assert login(app,role).get(path).status_code==200

def test_real_registration_login_and_role(app):
 c=app.test_client()
 r=post(c,'/auth/register/creator',dict(fullName='New Creator',emailAddress='new@example.com',password='Testing12345!',confirmPassword='Testing12345!',consent='y',platformFocus='YouTube',contentType='Travel'))
 assert r.status_code==302
 r=post(c,'/auth/login',dict(emailAddress='new@example.com',password='Testing12345!'))
 assert r.status_code==302 and '/creator/dashboard' in r.location
 assert c.get('/creator/dashboard').status_code==200
 assert c.get('/admin/dashboard').status_code==302

def test_csrf_blocks_mutation(app):
 c=login(app,'creator');j=job(app)
 assert c.post(f'/creator/jobs/{j}/select-editor',data={'editorId':1}).status_code==400

def test_session_uses_user_id_not_role_id(app):
 # Editor has user ID 2 and editor ID 1, the original collision trigger.
 c=login(app,'editor')
 assert c.get('/editor/dashboard').status_code==200
 assert c.get('/creator/dashboard').status_code==302

def test_suspension_revokes_existing_session(app):
 c=login(app,'editor')
 with app.app_context():
  User.query.filter_by(emailAddress='editor@example.com').first().isActive=False;db.session.commit()
 assert c.get('/editor/dashboard').status_code==302
 c2=app.test_client()
 r=post(c2,'/auth/login',dict(emailAddress='editor@example.com',password='Testing12345!'))
 assert r.status_code==200

def test_admin_registration_disabled(app):
 assert app.test_client().get('/auth/register/admin').status_code==404

def test_open_redirect_rejected(app):
 c=app.test_client();t=token(c,'/auth/login')
 r=c.post('/auth/login?next=//evil.example',data=dict(csrf_token=t,emailAddress='creator@example.com',password='Testing12345!'))
 assert r.location=='/creator/dashboard'

def test_complete_workflow(app):
 c=login(app,'creator');e=login(app,'editor');a=login(app,'admin')
 r=post(c,'/creator/jobs/new',dict(title='Cinematic travel video',description='Premiere Pro cinematic travel editor',budgetMin='100',budgetMax='300',deadline=(date.today()+timedelta(days=30)).isoformat(),requiredSkills='Premiere Pro'))
 assert r.status_code==302,r.text
 j=int(r.location.rsplit('/',1)[1]);assert c.get(r.location).status_code==200
 r=post(e,'/editor/portfolio/new',dict(title='Travel reel',description='Cinematic travel in Premiere Pro',videoUrl='https://example.com/reel',skillTags='Premiere Pro'))
 assert r.status_code==302,r.text
 pid=int(r.location.rsplit('/',1)[1])
 r=post(a,f'/admin/portfolios/{pid}/verify',dict(decision='approve',notes='Reviewed demo portfolio'))
 assert r.status_code==302
 with app.app_context():assert db.session.get(Portfolio,pid).editor.isVerified
 r=post(e,f'/editor/jobs/{j}/apply',dict(proposedRate='150',proposedTimeline='5 days',customProposal='I can edit cinematic travel videos.'))
 assert r.status_code==302,r.text
 aid=int(r.location.rsplit('/',1)[1]);assert e.get('/editor/applications').status_code==200
 assert e.get(f'/editor/applications/{aid}/edit').status_code==200
 assert c.get(f'/creator/jobs/{j}/applications').status_code==200
 r=post(c,f'/creator/jobs/{j}/select-editor',dict(editorId='1'),f'/creator/jobs/{j}')
 assert r.status_code==302
 with app.app_context():assert db.session.get(Job,j).status=='in_progress'
 r=post(e,f'/editor/projects/{j}/upload-deliverable',dict(deliverableUrl='https://example.com/final.mp4'))
 assert r.status_code==302,r.text
 r=post(c,f'/creator/jobs/{j}/complete',dict(deliverableUrl='https://example.com/final.mp4',completionNotes='Reviewed'))
 assert r.status_code==302
 with app.app_context():assert db.session.get(Job,j).status=='completed'
 r=post(c,'/creator/messages/send',dict(receiverId='2',jobId=str(j),subject='Thanks',messageContent='Great work'))
 assert r.status_code==302
 with app.app_context():assert Message.query.count()==1
 r=post(c,'/creator/ratings/submit',dict(jobId=str(j),rateeId='2',ratingValue='5',reviewText='Excellent work'))
 assert r.status_code==302,r.text
 with app.app_context():assert Rating.query.count()==1
 r=post(c,f'/creator/payments/initiate/{j}',dict(jobId=str(j),agreedAmount='150'))
 assert r.status_code==302,r.text
 with app.app_context():pay=Payment.query.one();payid=pay.paymentId;assert pay.status=='agreed'
 r=post(c,f'/creator/payments/process/{payid}',{})
 assert r.status_code==302
 with app.app_context():assert db.session.get(Payment,payid).status=='agreed'

def test_cross_account_job_denied(app):
 j=job(app);c=login(app,'other')
 assert c.get(f'/creator/jobs/{j}').status_code==302
 r=post(c,f'/creator/jobs/{j}/edit',dict(title='Hacked'),'/creator/jobs/new')
 assert r.status_code==302
 with app.app_context():assert db.session.get(Job,j).title=='Travel editing'

def test_rating_requires_actual_participants(app):
 j=job(app)
 with app.app_context():
  x=db.session.get(Job,j);x.status='completed';x.selectedEditorId=1;db.session.commit()
  assert Rating.createRating(j,4,2,5) is None
  assert Rating.createRating(j,1,1,5) is None
  assert Rating.createRating(j,1,2,5)
  assert Rating.createRating(j,1,2,5) is None

def test_password_reset_token_one_use_and_expiry(app):
 with app.app_context():
  t=PasswordResetToken.generateToken(1);value=t.token
 c=app.test_client()
 r=post(c,f'/auth/password-reset/{value}',dict(password='Changed12345!',confirmPassword='Changed12345!'))
 assert r.status_code==302
 with app.app_context():
  assert db.session.get(User,1).verifyPassword('Changed12345!')
  assert PasswordResetToken.validateToken(value) is None
  t=PasswordResetToken.generateToken(1);t.expiresAt=datetime.utcnow()-timedelta(seconds=1);db.session.commit()
  assert PasswordResetToken.validateToken(t.token) is None

def test_payment_gateway_never_contacted(app,monkeypatch):
 import requests
 def forbidden(*a,**kw):raise AssertionError('External network attempted')
 monkeypatch.setattr(requests,'get',forbidden);monkeypatch.setattr(requests,'post',forbidden)
 with app.app_context():
  from utilities.pesapal_payment import get_access_token
  assert 'error' in get_access_token()
 assert app.test_client().get('/creator/payments/pesapal/callback?OrderTrackingId=fake').status_code==503

def test_job_edit_refreshes_nlp(app):
 j=job(app)
 with app.app_context():
  x=db.session.get(Job,j);assert x.updateJobDetails(description='CapCut gaming fast paced')
  assert 'CapCut' in x.extractedSkills and 'gaming' in x.extractedNiches

def test_unrelated_job_message_rejected(app):
 j=job(app)
 with app.app_context():
  with pytest.raises(ValueError):Message.sendMessage(4,2,'Unrelated',jobId=j)

def test_nlp_matching():
 from app.nlp.job_parser import parse_job_description
 from app.nlp.editor_matcher import calculate_match_score
 p=parse_job_description('Cinematic travel editing with Premiere Pro and Premiere Pro')
 assert p['skills']==['Adobe Premiere Pro'] and p['styles']==['cinematic'] and p['niches']==['travel']
 assert calculate_match_score(p,p)==100
 assert calculate_match_score(p,{'skills':[]})==0
 with pytest.raises(ValueError):parse_job_description('')

def test_approved_portfolio_edit_blocked_and_delete_revokes_verification(app):
 with app.app_context():
  e=db.session.get(Editor,1)
  p=e.addPortfolioItem(dict(title='Original',description='Reviewed work',videoUrl='https://example.com/reel',skillTags='Premiere Pro'))
  pid=p.portfolioId
  db.session.get(Admin,1).verifyPortfolio(pid,True)
  assert e.isVerified
 c=login(app,'editor')
 r=post(c,f'/editor/portfolio/{pid}/edit',dict(title='Changed',description='Changed evidence',videoUrl='https://example.com/new',skillTags='CapCut'),'/editor/portfolio/new')
 assert r.status_code==302
 with app.app_context():
  assert db.session.get(Portfolio,pid).verificationStatus=='approved'
  assert db.session.get(Portfolio,pid).title=='Original'
 r=post(c,f'/editor/portfolio/{pid}/delete',{},f'/editor/portfolio/{pid}')
 assert r.status_code==302
 with app.app_context():
  assert db.session.get(Portfolio,pid) is None
  assert not db.session.get(Editor,1).isVerified

def test_unapplied_editor_cannot_be_selected(app):
 j=job(app)
 with app.app_context():
  x=db.session.get(Job,j)
  assert not x.selectEditor(1)
  assert x.status=='posted'
