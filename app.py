from flask import Flask, render_template, request, session, url_for, redirect
app = Flask(__name__)

import pickle
import sklearn

@app.route('/predict', methods=['GET','POST'])
def predict():
  if request.method == 'GET':
   msg = 'コストパフォーマンスを予想したい宿泊プランの情報を入力して下さい'
   return render_template('predict.html', title='Predict Page', message=msg)
  
  if request.method == 'POST':
    # reg = pickle.load(open('./model/trained_model.pkl', 'rb'))
    prefs = request.form.get('prefs')
    reg = pickle.load(open(f'./model/trained_model{prefs}.pkl', 'rb'))
    z = int(request.form['price'])
    x1 = request.form['bf']
    x2 = request.form['dinner']
    x3 = request.form['area']
    


    roomtype = request.form.get('roomtype')
    if roomtype == 'a':
      x4 = 1
      x5 = 0
      x6 = 0
      x7 = 0
      x8 = 0
      x9 = 0
      x10 = 0
      x11 = 0
      x12 = 0
    elif roomtype == 'b':
      x4 = 0
      x5 = 1
      x6 = 0
      x7 = 0
      x8 = 0
      x9 = 0
      x10 = 0
      x11 = 0
      x12 = 0
    elif roomtype == 'c':
      x4 = 0
      x5 = 0
      x6 = 1
      x7 = 0
      x8 = 0
      x9 = 0
      x10 = 0
      x11 = 0
      x12 = 0
    elif roomtype == 'd':
      x4 = 0
      x5 = 0
      x6 = 0
      x7 = 1
      x8 = 0
      x9 = 0
      x10 = 0
      x11 = 0
      x12 = 0
    elif roomtype == 'e':
      x4 = 0
      x5 = 0
      x6 = 0
      x7 = 0
      x8 = 1
      x9 = 0
      x10 = 0
      x11 = 0
      x12 = 0
    elif roomtype == 'f':
      x4 = 0
      x5 = 0
      x6 = 0
      x7 = 0
      x8 = 0
      x9 = 1
      x10 = 0
      x11 = 0
      x12 = 0
    elif roomtype == 'g':
      x4 = 0
      x5 = 0
      x6 = 0
      x7 = 0
      x8 = 0
      x9 = 0
      x10 = 1
      x11 = 0
      x12 = 0
    elif roomtype == 'h':
      x4 = 0
      x5 = 0
      x6 = 0
      x7 = 0
      x8 = 0
      x9 = 0
      x10 = 0
      x11 = 1
      x12 = 0
    else :
      x4 = 0
      x5 = 0
      x6 = 0
      x7 = 0
      x8 = 0
      x9 = 0
      x10 = 0
      x11 = 0
      x12 = 1
 
    x = [[int(x1), int(x2), int(x3), x4, x5, x6, x7 ,x8 ,x9 ,x10 ,x11 ,x12 ]]
    price = reg.predict(x)
    price = price[0][0]
    price = int(price)
    difference = z - price
    if difference >= 0:
      price = 'この宿泊プランは予想価格より{}円高いです。'.format(difference)
    else:
      difference = abs(difference)
      price = 'この宿泊プランは予想価格より{}円安いです。'.format(difference)
    return render_template('predict.html', title='Predict Page', message=price, bf=x1, dinner=x2, area=x3, price=z)
  
@app.route('/')
def index():  
  return render_template('predict.html')
 
if __name__ == '__main__':
  app.run(host='localhost', debug=True)