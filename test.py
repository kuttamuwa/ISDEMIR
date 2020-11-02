import yagmail

yag = yagmail.SMTP(user='hektasmail@gmail.com', password='figo1190')
yag.send(to='ucok.umut@gmail.com', subject='Testing yagmail', contents='working')

