import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


        

### Function to send the email ###
def send_an_email():
    toaddr = 'muhamedabdlnapy@gmail.com'    
    me = 'muhamedabdlnapy@gmail.com' 
    subject = "--Camera Alert--"

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = toaddr
    msg.preamble = "test " 
   
    
    part = MIMEBase('application', "octet-stream")
    part.set_payload(open("detection-.jpg", "rb").read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename= "detection-.jpg"')
    msg.attach(part)

    try:
       s = smtplib.SMTP('smtp.gmail.com', 587)
       s.ehlo()
       s.starttls()
       s.ehlo()
       s.login(user = 'muhamedabdlnapy@gmail.com', password = 'Hamada1211')
       s.sendmail(me, toaddr, msg.as_string())
       s.quit()
    except:
      print ("Error: unable to send email")
  

send_an_email()