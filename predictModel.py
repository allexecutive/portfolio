import requests
from bs4 import BeautifulSoup
import unicodedata
import re
import pandas as pd
import numpy as np
import time
import pickle
from sklearn import linear_model

url_tail = ['hokkaido/p{}','aomori/p{}','iwate/p{}','miyagi/p{}','akita/p{}','yamagata/p{}','fukushima/p{}',
            'ibaraki/p{}','tochigi/p{}','gunma/p{}','saitama/p{}','chiba/p{}','tokyo/p{}','kanagawa/p{}',
            'niigata/p{}','toyama/p{}','ishikawa/p{}','fukui/p{}','yamanashi/p{}','nagano/p{}','gifu/p{}',
            'shizuoka/p{}','aichi/p{}','mie/p{}','shiga/p{}','kyoto/p{}','osaka/p{}','hyogo/p{}',
            'nara/p{}','wakayama/p{}','tottori/p{}','shimane/p{}','okayama/p{}','hiroshima/p{}','yamaguchi/p{}',
            'tokushima/p{}','kagawa/p{}','ehime/p{}','kochi/p{}','fukuoka/p{}','saga/p{}','nagasaki/p{}',
            'kumamoto/p{}','oita/p{}','miyazaki/p{}','kagoshima/p{}','okinawa/p{}']
price_url = "https://hotel.travel.rakuten.co.jp/hotelinfo/plan/{0}"


# 文字列を正規化する
def normalize_text(text):
    return unicodedata.normalize("NFKC", text)

# htmlを取得
def get_html(url):
    print(url)
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    return soup

# 宿泊プランの情報を取得
def get_plan_and_room(hotelId):
    soup = get_html(price_url.format(hotelId))

    all_data = []

    # get plan list
    for plan in soup.findAll("li", {"class": "planThumb"})[:5]: # プランが多すぎる場合を考慮して5つまでに制御

        # get room list
        for room in plan.findAll("li", {"class": "rm-type-wrapper"}):
            room_data = d.copy()
            roomInfo = room.find("dd", {"class": "htlPlnTypTxt"})
            # room type
            roomTypeInfo = roomInfo.find("span", {"data-locate": "roomType-Info"})
            
            try:
                room_data["ルームタイプ"] = normalize_text(roomTypeInfo.find("strong").getText().strip())
            except AttributeError:
                room_data["ルームタイプ"]='なし'

            # meal
            roomMealInfo = roomInfo.find("span", {"data-locate": "roomType-option-meal"})
            room_data["食事"] = normalize_text(roomMealInfo.getText().replace("食事", "").strip())
            # area
            room_data["面積"] = normalize_text(roomTypeInfo.getText().replace(room_data["ルームタイプ"], "").strip())

            for li in room.find("ul", {"class": "htlPlnRmTypPrc"}).findAll("li"):
                row_data = room_data.copy()
                row_data["人数"] = normalize_text(li.find("dt").getText()).splitlines()[0]
                row_data["価格"] = normalize_text(li.find("dt").find("strong").getText())
                all_data.append(row_data)
    return pd.DataFrame(all_data)


for prefectureId in range(47):
    hotel_list_url = "https://search.travel.rakuten.co.jp/ds/yado/" + url_tail[prefectureId]
    all_data = []
    is_next_page_available = True
    page = 1
    
    # 次ページがなくなるまでループ
    while is_next_page_available:
        # get html
        soup = get_html(hotel_list_url.format(page))

        # extract hotels
        for hotel in soup.find("ul", {"id": "htlBox"}).findAll("h1"):
            d = {}
            d["hotelId"] = re.findall(string=hotel.find("a").get("href"), pattern=r"HOTEL/([0-9]+)")[0]
            d['prefectureId'] = prefectureId
            all_data.append(d)

        # check next page
        if soup.find("li", {"class": "pagingBack"}):
            page+=1
            time.sleep(1) # サーバへの負荷を考慮して1秒待ってから次に進む
        else:
            is_next_page_available = False
            
    df_hotel = pd.DataFrame(all_data)
    plan_room_data = []

    for i in range(len(df_hotel)):
        print("{}/{}".format(i+1, len(df_hotel)))
        hotel_row = df_hotel.iloc[i]
        hotelId = hotel_row["hotelId"]
        # price data
        df_plan_room = get_plan_and_room(hotelId)
        plan_room_data.append(df_plan_room)
        time.sleep(1)
        
    df_plan_room = pd.concat(plan_room_data, ignore_index=True)


    # 食事を朝食夕食の有無で分類
    df_plan_room["朝食"]=df_plan_room["食事"].str.contains('朝食あり').astype(int)
    df_plan_room["夕食"]=df_plan_room["食事"].str.contains('夕食あり').astype(int)
    # 面積のみ抽出
    m2_data=[]
    drop_index=[]
    area=df_plan_room['面積']

    for i in range(len(df_plan_room)):
    
        # 単位をm2に変換
        if '畳' in area[i]:
            array=area[i].split('畳')
            m2_data.append(float(array[0])*1.62)
        elif 'm' in area[i]:
            array=area[i].split('m')
            m2_data.append(float(array[0]))
        # 面積の表記がないindexを抽出
        else:
            m2_data.append(float(0))
            drop_index.append(i)

    m2=pd.DataFrame(m2_data)
    df_plan_room['平米']=m2
    # プランの平均価格を抽出
    aveprice_data=[]
    price=df_plan_room['価格']

    for i in range(len(df_plan_room)):
        number=price[i][:-3].replace(',','') 
        
        if '~' in number:
            array=number.split('~')
            heikin=(int(array[0])+int(array[1]))//2
        else:
            heikin=int(number)
            
        aveprice_data.append(heikin)
        
    aveprice=pd.DataFrame(aveprice_data)
    df_plan_room['平均価格']=aveprice
    # 利用人数が2名以下のプランを抽出
    num_data=[]
    num=df_plan_room['人数']

    # 利用人数の数値のみ抽出
    for i in range(len(df_plan_room)):
        m=re.search(r'\d',num[i])
        num_data.append(int(m.group()))

        # 利用人数が3以上のindexを抽出
        if num_data[i]>2:
            drop_index.append(i)

    # ルームタイプをダミー変換
    room_type=pd.get_dummies(df_plan_room['ルームタイプ'])
    df_plan_room_all= pd.concat([df_plan_room, room_type], axis=1)

    # ルームタイプの表記がないindexを抽出
    if any(df_plan_room_all.columns=='なし'):
        
        for i in range(len(df_plan_room)):

            if df_plan_room_all['なし'][i]==1:
                drop_index.append(i)
                
    # 洋室というルームタイプのindexを抽出
    if any(df_plan_room_all.columns=='洋室'):
        
        for i in range(len(df_plan_room)):

            if df_plan_room_all['洋室'][i]==1:
                drop_index.append(i)

    # 不必要な列を削除
    if any(df_plan_room_all.columns=='なし'):
        df_plan_room_part=df_plan_room_all.drop(['なし'], axis=1)
        
    if any(df_plan_room_all.columns=='洋室'):
        df_plan_room_part=df_plan_room_all.drop(['洋室'], axis=1)
        
    df_plan_room_part=df_plan_room_all.drop(['hotelId','prefectureId','ルームタイプ','食事','面積','人数','価格','その他'], axis=1)      
    # 欠損のあるデータを削除
    drop_index=list(set(drop_index))
    df_plan_room_part.drop(drop_index,inplace=True)
    df_plan_room_part.reset_index(inplace=True, drop=True)
    # データを保存
    df_plan_room_part.to_csv(f'Part[{prefectureId}].csv')
    # 平米の上下5%を外れ値として処理
    lower_m2=np.percentile(df_plan_room_part["平米"].dropna(),5)
    upper_m2=np.percentile(df_plan_room_part["平米"].dropna(),95)
    df_plan_room_part = df_plan_room_part[(df_plan_room_part["平米"]>=lower_m2) & (df_plan_room_part["平米"]<=upper_m2)]
    # 平均価格の上下1%を外れ値として処理
    lower_price = np.percentile(df_plan_room_part["平均価格"], 1)
    upper_price = np.percentile(df_plan_room_part["平均価格"], 99)
    df_plan_room_part = df_plan_room_part[(df_plan_room_part["平均価格"]>=lower_price) & (df_plan_room_part["平均価格"]<=upper_price)] 

    Y = df_plan_room_part[['平均価格']] # 目的変数を定義する
    X = df_plan_room_part.drop(['平均価格'], axis=1) # 説明変数を定義する
    reg = linear_model.LinearRegression() # モデルのクラスからモデルインスタンスを生成する
    reg.fit(X,Y) # 生成したインスタンスに目的変数と説明変数を指定する
    file = f'trained_model{prefectureId}.pkl' 
    pickle.dump(reg, open(file, 'wb')) # 予測モデルを保存
    print(f'{prefectureId}'+'-'*100+f'{prefectureId}')