import numpy as np
import psycopg2
from config import config

class Parser_logs:
    def __init__(self):
        # действия в логах
        self.val_list_act=["empty", "only categories", "cart", "pay", "success_pay"]
        # файл парсинга
        self.fileName="logs.txt"
        self.cur,self.conn=self.connect()

    # подключаемся к базе
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

    	# execute a statement
            # print('PostgreSQL database version:')
            # cur.execute('SELECT version()')

            # # display the PostgreSQL database server version
            # db_version = cur.fetchone()
            # print(db_version)

    	# close the communication with the PostgreSQL
            # cur.close()


        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        # finally:
        #     if conn is not None:
        #         conn.close()
        #         print('Database connection closed.')

        return cur,conn


    # read file and return strings list
    def read_file(self):
        try:
            with open(self.fileName, 'r') as file:
                textLines=file.readlines()

            return textLines
        except error as e:
            print(e)

    # check exist data to table
    def check_row(self, tbl_name,clm_name,value, cur):
        request="SELECT EXISTS(SELECT 1 FROM "+tbl_name+" WHERE "+clm_name+" = '"+value+"');"

        cur.execute(request)
        data = cur.fetchall()

        return data[0][0]

    # add data into table
    def add_data(self, tbl_name, clm_name, value, cur, conn):
        request="INSERT INTO "+tbl_name+"("+clm_name+") VALUES ("+value+")"
        cur.execute(request)
        conn.commit()
        # try:
        #     cur.execute(request)
        #
        # except (Exception, psycopg2.DatabaseError) as error:
        #     print(error)

    # update data into table
    def update_data(self, tbl_name, clm_value, cond, cur, conn):
        request="UPDATE "+tbl_name+" SET "+clm_value+" WHERE "+cond+";"
        cur.execute(request)
        conn.commit()

    # get id categories to subcat
    def get_id_cat(self, value, cur):
        request="SELECT id_cat FROM categories WHERE cat_name='"+value+"'"
        cur.execute(request)
        data = cur.fetchall()

        return data[0][0]

    def addViews(self, splitStr, slash_splt, act):
        # check if the views added to table
        table_name='views'
        clm_name='id_view'
        id_dt=splitStr[4][1:-1]

        ch_dt=self.check_row(table_name,clm_name,id_dt,self.cur)

        if not ch_dt:
            clms_name='id_view, time_view, ip_view, id_action, data_view'
            values="'"+id_dt+"', '"+splitStr[3]+"', '"+splitStr[6]+"', "+str(act)+",'"+splitStr[2]+"'"

            self.add_data(table_name, clms_name, values, self.cur,self.conn)
            print("View added!")

            # add categories
            if act==2:
                table_name='categories'
                clm_name='cat_name'
                val=slash_splt[3]

                # categoria doesn't exist?
                if not self.check_row(table_name,clm_name,val,self.cur):
                    clms_name='cat_name'
                    values="'"+val+"'"
                    self.add_data(table_name, clms_name, values, self.cur,self.conn)
                    print("Categoria added!")

                    id_cat=self.get_id_cat(val, self.cur)
                    table_name='views_cats'
                    clm_name='id_view,id_cat'
                    val="'"+id_dt+"',"+str(id_cat)

                    self.add_data(table_name, clm_name, val, self.cur,self.conn)

                # for subcategories. Added subcat
                if len(slash_splt)==6:

                    # id main categoria
                    id_cat=self.get_id_cat(val, self.cur)
                    print(slash_splt[4], id_cat)
                    table_name='categories'
                    clm_name='cat_name, id_subcat'

                    val="'"+slash_splt[4]+"',"+str(id_cat)

                    self.add_data(table_name, clm_name, val, self.cur,self.conn)

                    table_name='views_cats'
                    clm_name='id_view,id_cat'
                    val="'"+id_dt+"',"+str(id_cat)
                    self.add_data(table_name, clm_name, val, self.cur,self.conn)

                    print("Subcategoria added!")
            # add cart
            elif act==3:
                last_item=slash_splt[-1]

                am_split=last_item[5:].split("&")
                good_id=am_split[0][9:]
                amount=am_split[1][7:]
                cart_id=am_split[2][8:]

                # add good into goods
                table_name='goods'
                clm_name='id_good'
                val=good_id
                print(good_id)
                if not self.check_row(table_name,clm_name,val,self.cur):
                    self.add_data(table_name, clm_name, val, self.cur,self.conn)

                # add data into carts
                table_name='carts'
                clm_name='id_cart'
                val=cart_id

                if not self.check_row(table_name,clm_name,val,self.cur):
                    self.add_data(table_name, clm_name, val, self.cur,self.conn)

                # add data into goods in carts
                table_name='goods_in_carts'
                clm_name='id_good, amount, id_cart'
                val=good_id+","+amount+","+cart_id

                self.add_data(table_name, clm_name, val, self.cur,self.conn)
            # add pay
            elif act==4:
                last_item=slash_splt[-1]

                am_split=last_item[3:].split("&")
                user_id=am_split[0][9:]
                cart_id=am_split[1][8:]
                last_ip=splitStr[6]

                # add user info
                table_name='users'
                clm_name='id_user'
                val=user_id

                if not self.check_row(table_name,clm_name,val,self.cur):
                    table_name='users'
                    clm_name='id_user, last_ip'
                    val=user_id+", '"+last_ip+"'"
                    self.add_data(table_name, clm_name, val, self.cur,self.conn)

                # update pay info
                table_name='carts'
                clm_val="id_user="+user_id
                cond="id_cart="+cart_id
                self.update_data(table_name, clm_val, cond, self.cur,self.conn)

            # success pay
            elif act==5:
                cart_id=slash_splt[-2][12:]

                # update pay info
                table_name='carts'
                clm_val="pay=1"
                cond="id_cart="+cart_id
                self.update_data(table_name, clm_val, cond, self.cur,self.conn)

        else:
            print("Already exist")

    # parse string and process fields
    def parse_fields(self):
        all_str=[]
        # get info from files *.txt
        strs=self.read_file()
        listFields=[]
        for line in strs:
            splitStr=line.split()

            # print(splitStr[-1])
            slash_splt=splitStr[-1].split("/")

            # print(len(slash_splt[-1]))
            print(slash_splt)
            last_item=slash_splt[-1]

            # categories
            # act=1 - empty, act=2 - only categories, act=3 - cart, act=4 - pay, act=5 - success_pay
            if len(slash_splt)>4:
                # only categories or success_pay
                if slash_splt[-2].find('success_pay')>-1:
                    print('success_pay')
                    act=5


                else:
                    # add categories
                    print("Add cat")
                    act=2
            # action or empty
            else:
                # cart or pay
                if len(last_item)>0:
                    if last_item.find('cart?')>-1:
                        print("Cart: "+str(last_item.find('cart?')))
                        act=3
                    else:
                        print("Pay: "+str(last_item.find('pay?')))
                        act=4
                else:
                    # empty action
                    print("empty:")
                    act=1
            print(act)
            # check action
            tbl_name="actions"
            clm_name="id_action"

            ch_act=self.check_row(tbl_name,clm_name,str(act),self.cur)
            if not ch_act:

                tbl_name_act="actions"
                clm_name_act="id_action, act_name"
                vl_act=str(act)+",'"+self.val_list_act[act-1]+"'"
                self.add_data(tbl_name_act, clm_name_act, vl_act, self.cur,self.conn)

            # add views and action
            self.addViews(splitStr,slash_splt,act)
            print("\n")

pL=Parser_logs()
pL.parse_fields()
