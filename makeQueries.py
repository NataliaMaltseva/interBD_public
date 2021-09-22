import numpy as np
import psycopg2
from config import config
import os
import requests
import json

class Queries:
    def connect(self):
        """ Connect to the PostgreSQL database server """
        conn = None

        try:
            # read connection parameters
            params = config()

            # connect to the PostgreSQL server
            print('Connecting to the PostgreSQL database...')
            conn = psycopg2.connect(**params)

            # create a cursor
            cur = conn.cursor()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

        # finally:
        #     if conn is not None:
        #         conn.close()
        #         print('Database connection closed.')

        return cur,conn

    # get country by user ip
    def get_country_name_by_ip(self, ip_address):
        # URL to send the request to
        request_url = 'https://geolocation-db.com/jsonp/' + ip_address
        # Send request and decode the result
        response = requests.get(request_url)
        result = response.content.decode()
        # Clean the returned string so it just contains the dictionary data for the IP address
        result = result.split("(")[1].strip(")")
        # Convert this data into a dictionary
        result  = json.loads(result)

        return result['country_name']

    # make queries
    def make_queries(self):
        cur,conn=self.connect()

        # 1. Из какой страны пользователь
        q1="select count(*) as cnt, ip_view from views group by ip_view order by cnt desc limit 1;"
        res1=cur.execute(q1)
        data_res1=cur.fetchall()
        ip=data_res1[0][1]
        country_name=self.get_country_name_by_ip(ip)
        print("1. More often users ip: "+ip+" from "+country_name+".")

        # 2. Посетители из какой страны чаще всего интересуются товарами из определенной категории “fresh_fish”
        # long time execute!
        param_q1='fresh_fish'
        param_q1='frozen_fish'
        q2="select views.id_view, views.ip_view, views_cats.id_cat, categories.cat_name from views inner join views_cats on views_cats.id_view=views.id_view  inner join categories on views_cats.id_cat=categories.id_cat  where categories.cat_name='"+param_q1+"';"
        res1=cur.execute(q2)
        data_res2=cur.fetchall()
        list_country=[]

        for d_row in data_res2:
            list_country.append(self.get_country_name_by_ip(d_row[1]))

        duplicate_frequencies = {}
        for i in set(list_country):
            duplicate_frequencies[i] = list_country.count(i)

        sort_duplFreq = sorted(duplicate_frequencies.items(), key=lambda x: x[1])
        print("2. More often users country from category {0} - {1}".format(param_q1,sort_duplFreq[-1][0]))

        # 3. В какое время суток чаще всего просматривают категорию “frozen_fish”
        # уточнить время суток
        param_q3='frozen_fish'
        q3="select SUM(CASE WHEN CAST(views.time_view AS Time) >= '06:00:00' AND CAST(views.time_view AS Time) < '10:00:00' THEN 1 ELSE 0 END) as morning, SUM(CASE WHEN CAST(views.time_view AS Time) >= '10:00:00' AND CAST(views.time_view AS Time) < '18:00:00' THEN 1 ELSE 0 END) as day_t, SUM(CASE WHEN CAST(views.time_view AS Time) >= '18:00:00' AND CAST(views.time_view AS Time) < '00:00:00' THEN 1 ELSE 0 END)  as evening, SUM(CASE WHEN CAST(views.time_view AS Time) >= '00:00:00' AND CAST(views.time_view AS Time) < '06:00:00'  THEN 1 ELSE 0 END) as night from views inner join views_cats on views_cats.id_view=views.id_view  inner join categories on views_cats.id_cat=categories.id_cat where categories.cat_name='"+param_q3+"';"
        res3=cur.execute(q3)
        data_res3=cur.fetchall()
        time_freq={'Morning':data_res3[0][0],
        'Day':data_res3[0][1],
        'Evening':data_res3[0][2],
        'Night': data_res3[0][3] }

        sort_time_freg = sorted(time_freq.items(), key=lambda x: x[1])
        print("3. More often time from categories {0}: {1}".format(param_q3,sort_time_freg[-1][0]))

        # 4. Какое максимальное число запросов на сайт за астрономический час (c 00 минут 00 секунд до 59 минут 59 секунд)?
        # как вариант можно сделать  так
        q4="SELECT DATE_PART('hour',time_view), Count(*) as cnt FROM views GROUP BY DATE_PART('hour',time_view) ORDER BY cnt DESC LIMIT 1"
        res4=cur.execute(q4)
        data_res4=cur.fetchall()
        print("4. Max count ({0}) request at {1} to {2}:".format(data_res4[0][0], data_res4[0][1],data_res4[0][0]))

        # 5. Товары из какой категории чаще всего покупают совместно с товаром из категории “semi_manufactures”
        # нет таблицы соответствия между товаром и категорией, поэтому запрос выдает просмотры категорий по ip адресам
        param_q5='semi_manufactures'
        q5_1="select views.ip_view, views_cats.id_cat, categories.cat_name from views inner join views_cats on views_cats.id_view=views.id_view  inner join categories on views_cats.id_cat=categories.id_cat where categories.cat_name='"+param_q5+"';"
        res5_1=cur.execute(q5_1)
        data_res5_1=cur.fetchall()
        cat_name={}
        print("4. Categories with semi_manufactures:")
        for dt5_1 in data_res5_1:
            ip_dt5_1=dt5_1[0]
            param_q5_2=ip_dt5_1
            q5_2="select categories.cat_name, count(views.ip_view) from views inner join views_cats on views_cats.id_view=views.id_view  inner join categories on views_cats.id_cat=categories.id_cat where categories.cat_name!='semi_manufactures' and ip_view='121.165.118.201' group by categories.cat_name;"
            res5_2=cur.execute(q5_2)
            data_res5_2=cur.fetchall()
            for dt5_2 in data_res5_2:
                cat_name[dt5_2[0]]=1

        for c_t in cat_name:
            print(c_t)

        # 6. Сколько не оплаченных корзин имеется
        q6="select count(*) from carts where pay is null"
        res6=cur.execute(q6)
        count=cur.fetchone()
        print("6. Count carts without pay: {0:d}".format(count[0]))

        # 7. Count user buy twice
        # q7="select count(*) as creq from (select count(*) as cnt from carts where pay is not null group by id_user) as foo"
        q7="select count(*) as cnt from carts where pay is not null group by id_user having count(*)>1"
        res6=cur.execute(q7)
        count=cur.fetchone()
        print("7. Count users bought again: {0:d}".format(count[0]))

mQ=Queries()
mQ.make_queries()
