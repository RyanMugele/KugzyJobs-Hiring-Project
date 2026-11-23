from app import create_app,db
from app.models.user import User
from app.models import Creator,Editor,Admin,Job,Portfolio,JobApplication,Payment,Report
from datetime import date,timedelta
app=create_app('testing')
app.config['WTF_CSRF_ENABLED']=False
with app.app_context():
 db.create_all()
 users={}
 for role,cls in [('creator',Creator),('editor',Editor),('admin',Admin)]:
  u=User(fullName=role.title()+' Demo',emailAddress=role+'@example.com',userType=role,password='Testing12345!')
  db.session.add(u);db.session.flush();db.session.add(cls(userId=u.userId));users[role]=u
 db.session.commit()
 c=users['creator'].creator;e=users['editor'].editor
 job=c.postJob(dict(title='Cinematic travel video',description='Premiere Pro cinematic travel editing',budgetMin=100,budgetMax=300,deadline=date.today()+timedelta(days=30)))
 portfolio=e.addPortfolioItem(dict(title='Travel demo',description='Cinematic travel videos',videoUrl='https://example.com/demo',skillTags='Premiere Pro'))
 application=JobApplication(jobId=job.jobId,editorId=e.editorId,proposedRate=150)
 db.session.add(application);db.session.commit()
 payment=Payment.createPaymentAgreement(job.jobId,150)
 report=Report(reporterId=users['creator'].userId,reportedUserId=users['editor'].userId,reason='Test report') if False else None
 ids={'job_id':job.jobId,'portfolio_id':portfolio.portfolioId,'application_id':application.jobApplicationId,'payment_id':payment.paymentId,'user_id':users['editor'].userId,'editor_id':e.editorId}
 users = {k:v.userId for k,v in users.items()}
for role,u in [('anonymous',None)]+list(users.items()):
 client=app.test_client()
 if u:
  with client.session_transaction() as ses:ses['_user_id']=str(u);ses['_fresh']=True;ses['user_type']=role
 for rule in app.url_map.iter_rules():
  if 'GET' not in rule.methods or rule.endpoint=='static':continue
  if rule.endpoint.startswith(('creator.','editor.','admin.')) and not rule.endpoint.startswith(role+'.'):continue
  if any(a not in ids for a in rule.arguments):continue
  if rule.endpoint in ['authentication.logout','authentication.reauthenticate']:continue
  from flask import url_for
  with app.test_request_context():url=url_for(rule.endpoint,**{k:ids[k] for k in rule.arguments})
  try:
   res=client.get(url)
   print(role,res.status_code,url)
  except Exception as ex:
   print('FAIL',role,url,type(ex).__name__,str(ex))
