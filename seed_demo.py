"""Create clearly fictional demonstration accounts, leaving existing users alone."""
import getpass
import os
from datetime import date,timedelta
from flasky import app
from app import db
from app.models.user import User
from app.models import Creator,Editor,Admin
from app.nlp.job_parser import parse_job_description

def seed(password):
 if len(password)<12:raise ValueError('Use a demo password of at least 12 characters.')
 with app.app_context():
  db.create_all()
  for role,cls in [('creator',Creator),('editor',Editor),('admin',Admin)]:
   email=f'{role}@demo.example.com'
   if User.query.filter_by(emailAddress=email).first():continue
   u=User(fullName=f'Demo {role.title()}',emailAddress=email,userType=role,password=password)
   db.session.add(u);db.session.flush()
   kwargs={'specializations':'Adobe Premiere Pro, Color Grading','experienceLevel':'intermediate','hourlyRate':35} if role=='editor' else {}
   db.session.add(cls(userId=u.userId,**kwargs));db.session.commit()
  c=User.query.filter_by(emailAddress='creator@demo.example.com').first().creator
  if not c.jobs:
   description='Seeking a cinematic travel editor with Adobe Premiere Pro and color grading skills.'
   c.postJob(dict(title='Cinematic travel film — demonstration',description=description,budgetMin=150,budgetMax=300,deadline=date.today()+timedelta(days=30),requiredSkills='Premiere Pro, Color Grading',**{'extracted'+k.title():v for k,v in parse_job_description(description).items()}))
  e=User.query.filter_by(emailAddress='editor@demo.example.com').first().editor
  if not e.portfolios:
   e.addPortfolioItem(dict(title='Travel reel — demonstration',description='Fictional portfolio entry for testing administrator review. Replace with your actual work.',videoUrl='https://example.com/demo-reel',skillTags='Premiere Pro, Color Grading'))
 print('Demo accounts: creator@demo.example.com, editor@demo.example.com, admin@demo.example.com')
 print('Use the demo password you supplied. All entries are fictional; no emails or payments are sent.')

if __name__=='__main__':seed(os.environ.get('KUGZY_DEMO_PASSWORD') or getpass.getpass('Choose a demo password (12+ characters): '))
