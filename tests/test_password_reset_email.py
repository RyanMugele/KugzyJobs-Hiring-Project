import re
from datetime import datetime,timedelta
from unittest.mock import patch
import pytest
from app import create_app,db
from app.models.user import User
from app.models import Creator,PasswordResetToken
from utilities.email_utils import send_email

@pytest.fixture
def reset_app():
 app=create_app('testing')
 app.config.update(EMAIL_ENABLED=True,PUBLIC_BASE_URL='https://kugzyjobs.onrender.com',MAIL_DEFAULT_SENDER='KugzyJobs <sender@example.org>')
 with app.app_context():
  db.create_all()
  u=User(fullName='Reset Test',emailAddress='reset@example.org',userType='creator',password='OriginalPassword123!')
  db.session.add(u);db.session.flush();db.session.add(Creator(userId=u.userId));db.session.commit()
 yield app
 with app.app_context():db.drop_all()

def submit(c,path,data):
 r=c.get(path);token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',r.text).group(1)
 return c.post(path,data=dict(data,csrf_token=token),follow_redirects=True)

def test_reset_email_and_changed_login(reset_app):
 c=reset_app.test_client()
 with patch('flask_mailman.EmailMultiAlternatives.send',return_value=1) as smtp:
  response=submit(c,'/auth/password-reset-request',dict(emailAddress='reset@example.org'))
  assert 'If an account exists' in response.text and smtp.call_count==1
 with reset_app.app_context():
  token=PasswordResetToken.query.one().token
 response=submit(c,f'/auth/password-reset/{token}',dict(password='ReplacementPassword123!',confirmPassword='ReplacementPassword123!'))
 assert 'updated successfully' in response.text
 with reset_app.app_context():
  user=User.query.one();assert user.verifyPassword('ReplacementPassword123!') and not user.verifyPassword('OriginalPassword123!')
 assert 'invalid or expired' in c.get(f'/auth/password-reset/{token}',follow_redirects=True).text
 result=submit(c,'/auth/login',dict(emailAddress='reset@example.org',password='ReplacementPassword123!'))
 assert 'Creator Dashboard' in result.text

def test_message_has_canonical_link_and_plaintext(reset_app):
 with reset_app.app_context(),patch('utilities.email_utils.EmailMultiAlternatives') as msg:
  msg.return_value.send.return_value=1
  assert send_email(['reset@example.org'],'Reset','email/password_reset_request',user_name='Reset Test',reset_link='https://kugzyjobs.onrender.com/auth/password-reset/test-token')
  call=msg.call_args.kwargs
  assert call['from_email']=='KugzyJobs <sender@example.org>'
  assert 'https://kugzyjobs.onrender.com/auth/password-reset/test-token' in call['body']
  assert '<p>' not in call['body']
  assert msg.return_value.attach_alternative.call_args.args[1]=='text/html'

def test_canonical_origin_ignores_request_host(reset_app):
 with patch('utilities.email_utils.send_email',return_value=True) as send:
  submit(reset_app.test_client(),'/auth/password-reset-request',dict(emailAddress='reset@example.org'))
  assert send.call_args.kwargs['reset_link'].startswith('https://kugzyjobs.onrender.com/auth/password-reset/')

def test_unknown_account_and_cooldown_share_response(reset_app):
 c=reset_app.test_client()
 with patch('utilities.email_utils.send_email',return_value=True) as send:
  known=submit(c,'/auth/password-reset-request',dict(emailAddress='reset@example.org'))
  submit(c,'/auth/password-reset-request',dict(emailAddress='reset@example.org'))
  unknown=submit(c,'/auth/password-reset-request',dict(emailAddress='missing@example.org'))
  assert send.call_count==1
  assert 'If an account exists' in known.text and 'If an account exists' in unknown.text
 with reset_app.app_context():assert PasswordResetToken.query.count()==1

def test_failed_delivery_invalidates_link(reset_app):
 with patch('flask_mailman.EmailMultiAlternatives.send',side_effect=RuntimeError('private provider detail')):
  response=submit(reset_app.test_client(),'/auth/password-reset-request',dict(emailAddress='reset@example.org'))
 assert 'private provider detail' not in response.text
 with reset_app.app_context():assert PasswordResetToken.query.one().isUsed

def test_disabled_delivery_does_not_generate_token(reset_app):
 reset_app.config['EMAIL_ENABLED']=False
 with patch('flask_mailman.EmailMultiAlternatives.send') as send:
  submit(reset_app.test_client(),'/auth/password-reset-request',dict(emailAddress='reset@example.org'))
  send.assert_not_called()
 with reset_app.app_context():assert PasswordResetToken.query.count()==0

def test_new_request_replaces_old_link_after_cooldown(reset_app):
 c=reset_app.test_client()
 with patch('utilities.email_utils.send_email',return_value=True):
  submit(c,'/auth/password-reset-request',dict(emailAddress='reset@example.org'))
  with reset_app.app_context():
   old=PasswordResetToken.query.one();token=old.token;old.dateCreated=datetime.utcnow()-timedelta(minutes=2);db.session.commit()
  submit(c,'/auth/password-reset-request',dict(emailAddress='reset@example.org'))
 with reset_app.app_context():
  assert PasswordResetToken.validateToken(token) is None
  assert PasswordResetToken.query.filter_by(isUsed=False).count()==1
