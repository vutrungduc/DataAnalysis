from datetime import datetime
import pandas as pd
import psycopg2
from pytrends.request import TrendReq
import matplotlib.pyplot as plt
import os
import platform

f_name = "keytrends"
date1 = datetime.now()
start_date = "2019-01-01"
end_date = date1.strftime('%Y-%m-%d')
date_check = ""
s_time_frame = start_date + " " + date_check
kw_list_file = pd.read_excel('keytrends.xlsx').dropna()
column_names = list(kw_list_file.columns)

def connect():
     conn, cur = None, None
     try:
          # print('Connecting to the PostgreSQL database...')
          conn = psycopg2.connect(
            host="localhost", port="5432",
            database="vn_trending",
            user="postgres",
            password="qazwsx1122")
          cur = conn.cursor()
     except (Exception, psycopg2.DatabaseError) as error:
          print("Error while excuting SQL" + error)
     return conn, cur

def input_data(f_name, date_check):
     global column_names
     s_time_frame = '2019-01-01'+' '+ date_check
     pytrend = TrendReq(hl='VN', tz=360)
     try:
          kw_list_file = pd.read_excel(f_name + '.xlsx').dropna()
          column_names = list(kw_list_file.columns)
          conn, cur = connect()
        # cur.execute("DROP TABLE IF EXISTS vn_trending;")
          cur.execute("""CREATE TABLE  IF NOT EXISTS vn_trending(
                              id int4 NOT NULL GENERATED BY DEFAULT AS IDENTITY  PRIMARY KEY,
                              date DATE,
                              keyword CHAR(100),
                              value INTEGER,
                              trend_type CHAR(100));"""
                    )
          conn.commit()
          print("Table created successfully, please wait...")

          table = 'vn_trending'
          columns = "keyword, date, value, trend_type"
          for column in column_names:
               dataset = []
               df = kw_list_file[column].values.tolist()
               for index in range(len(df)):
                    pytrend.build_payload(
                    kw_list=[df[index]],
                    cat=0, geo='VN',
                    timeframe=s_time_frame,
                    gprop='')
                    data = pytrend.interest_over_time()
                    if not data.empty:
                         data = data.drop(labels=['isPartial'], axis='columns')
                         dataset.append(data)

                         len_data = len(data)
                         keyw = data.columns[0]
                         keyws = len_data * [str(keyw).replace("'", "''")]
                         date1 = [dt.to_pydatetime().strftime('%Y-%m-%d %H:%M:%S') for dt in data.index]
                         val = [d[0] for d in data.values]
                         insert_stmt = ''
                         for i in range(len_data):
                              if val[i] > 0 and df[index] != 'NaN':
                                   values = "VALUES ('{}','{}','{}','{}')".format(keyws[i], date1[i], val[i], column)
                                   insert_stmt += "INSERT INTO {} ({}) ({});".format(table, columns, values)
                         cur.execute(insert_stmt)
                         conn.commit()
          conn.close()
     except Exception as ex:
          print(ex)

def top_10_trending():
     sql = """
          SELECT  A.keyword, A.sum_val, A.monthly
               FROM
               (SELECT keyword, sum(VALUE::INT) sum_val, to_char(date::date,'mm/yyyy') monthly
                FROM vn_trending
                GROUP BY keyword, to_char(date::date,'mm/yyyy')
                ORDER BY sum(VALUE::INT) DESC
                LIMIT 10
                    ) A
            ;"""
     conn, cur = connect()
     cur.execute(sql)
     rd = cur.fetchall()
     conn.close()
     cur.close()

     df = pd.DataFrame(rd, columns=['keyword','value', 'monthly'])
     df_new = df.rename(columns={'keyword': 'Keyword', 'value': 'Số lần tìm kiếm', 'monthly':'Tháng tìm kiếm nhiều nhất'})
     piv = df_new.pivot_table(index=["Keyword", "Tháng tìm kiếm nhiều nhất"], values=["Số lần tìm kiếm"], aggfunc='sum')
     writer = pd.ExcelWriter('vn_trending_top_10_2020.xlsx')

     df_new.to_excel(writer, index_label='STT', startcol=0, startrow = 2)
     worksheet = writer.sheets['Sheet1']
     workbook = writer.book
     cell_format = workbook.add_format({'size':15, 'align':'center'})
     worksheet.merge_range('A1:D1',"Danh sách từ khóa tìm kiếm tại Việt Nam",cell_format)
     worksheet.merge_range('A2:D2',"Năm 2020",cell_format)
     print("Xuất file báo cáo thành công !\n")
     writer.save()

def top_search_keyword_2020():
     columns = [col.replace('/ ','_') for col in column_names]
     writer = pd.ExcelWriter('vn_trending_search_keyword_2020.xlsx')
     for column in columns:
          sql = """
                 SELECT keyword
                 ,sum(case date_part('MONTH', date) when 1 then value else 0 end) as "Tháng 1"
                 ,sum(case date_part('MONTH', date) when 2 then value else 0 end) as "Tháng 2"
                 ,sum(case date_part('MONTH', date) when 3 then value else 0 end) as "Tháng 3"
                 ,sum(case date_part('MONTH', date) when 4 then value else 0 end) as "Tháng 4"
                 ,sum(case date_part('MONTH', date) when 5 then value else 0 end) as "Tháng 5"
                 ,sum(case date_part('MONTH', date) when 6 then value else 0 end) as "Tháng 6"
                 ,sum(case date_part('MONTH', date) when 7 then value else 0 end) as "Tháng 7"
                 ,sum(case date_part('MONTH', date) when 8 then value else 0 end) as "Tháng 8"
                 ,sum(case date_part('MONTH', date) when 9 then value else 0 end) as "Tháng 9"
                 ,sum(case date_part('MONTH', date) when 10 then value else 0 end) as "Tháng 10"
                 ,sum(case date_part('MONTH', date) when 11 then value else 0 end) as "Tháng 11"
                 ,sum(case date_part('MONTH', date) when 12 then value else 0 end) as "Tháng 12"
                 FROM vn_trending
                 WHERE date_part('YEAR',date) = 2020 and trend_type = '{}'
                 GROUP BY 1
                 ;""".format(column)
          conn, cur = connect()     
          cur.execute(sql)
          rd = cur.fetchall()
          conn.close()
          cur.close()

          df = pd.DataFrame(rd,columns=['Keyword', 'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6', 'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'])
          df.to_excel(writer, sheet_name=column, index_label='STT', startcol=0, startrow = 2)
          worksheet = writer.sheets[column]
          workbook = writer.book
          cell_format = workbook.add_format({'size':15, 'align':'center'})
          worksheet.merge_range('A1:N1',"Danh sách từ khóa tìm kiếm tại Việt Nam",cell_format)
          worksheet.merge_range('A2:N2',"Năm 2020",cell_format)

     print("Xuất báo cáo top search keyword 2020 thành công !\n")
     writer.save()

def line_chart_top5_2020():
     sql = """
                 SELECT keyword, sum(VALUE) sum_val
                 FROM vn_trending
                 WHERE date_part('YEAR',date) = 2020
                 GROUP BY keyword
                 ORDER BY sum(VALUE) DESC
                 LIMIT 5
                 ;"""
     conn, cur = connect()
     cur.execute(sql)
     rd = cur.fetchall()
     conn.close()
     cur.close()

     df = pd.DataFrame(rd, columns=['keyword','value'])
     keyword, value = zip(*rd)
     df['keyword'] = df['keyword'].str.strip() 
     keyword = df['keyword'].tolist() 
     df.value  = df.value.astype(int)
     ax = df.plot(x='keyword',y='value', figsize=(8,5), kind='line')
     plt.title("Từ khóa tìm kiếm nhiều nhất tại Việt Nam \n2020")
         
     fig = ax.get_figure()
     fig.savefig('line_chart_top5_2020.png')
     print("Xuất báo cáo line chart 2020 thành công !\n")

def bar_chart_top5_2019():
     sql = """
            SELECT keyword, sum(VALUE) sum_val
            FROM vn_trending
            WHERE date_part('YEAR',date) = 2019
            GROUP BY keyword
            ORDER BY sum(VALUE) DESC
            LIMIT 5
            ;"""
     conn, cur = connect()
     cur.execute(sql)
     rd = cur.fetchall()
     conn.close()
     cur.close()

     df = pd.DataFrame(rd, columns=['keyword','value'])
     keyword, value = zip(*rd)
     df['keyword'] = df['keyword'].str.strip() 
     keyword = df['keyword'].tolist() 
     df.value  = df.value.astype(int)
     ax = df.plot(x='keyword',y='value', figsize=(8,5), kind='bar')
     plt.xticks(rotation=0) 
     plt.title("Từ khóa tìm kiếm nhiều nhất tại Việt Nam \n2019")

     fig = ax.get_figure()
     fig.savefig('bar_chart_top5_2019.png')
     print("Xuất báo cáo bar chart 2019 thành công !\n")

def top_10_trending_2020():
     sql = """
            SELECT  A.keyword, A.sum_val, A.monthly
                FROM
                    (   SELECT keyword, sum(VALUE::INT) sum_val, to_char(date::date,'mm/yyyy') monthly
                        FROM vn_trending
                        WHERE EXTRACT(YEAR FROM DATE) = 2020
                        GROUP BY keyword, to_char(date::date,'mm/yyyy')
                        ORDER BY sum_val DESC
                        LIMIT 10
                    ) A
            ;"""
     sql2 = """
            SELECT  A.keyword, A.sum_val, A.monthly
                FROM
                    (   SELECT keyword, sum(VALUE::INT) sum_val, to_char(date::date,'mm/yyyy') monthly
                        FROM vn_trending
                        WHERE EXTRACT(YEAR FROM DATE) = 2019
                        GROUP BY keyword, to_char(date::date,'mm/yyyy')
                        ORDER BY sum_val DESC
                        LIMIT 10
                    ) A
            ;"""
     conn, cur = connect()
     cur.execute(sql)
     rd = cur.fetchall()

     cur.execute(sql2)
     rd2 = cur.fetchall()

     conn.close()
     cur.close()

     df = pd.DataFrame(rd, columns=['keyword','value', 'monthly'])
     df2 = pd.DataFrame(rd2, columns=['keyword','value', 'monthly'])

     df_new = df.rename(columns={'keyword': 'Keyword', 'value': 'Số lần tìm kiếm', 'monthly':'Tháng tìm kiếm nhiều nhất'})
     df_new2 = df2.rename(columns={'keyword': 'Keyword', 'value': 'Số lần tìm kiếm', 'monthly':'Tháng tìm kiếm nhiều nhất'})
    
     piv = df_new.pivot_table(index=["Keyword", "Tháng tìm kiếm nhiều nhất"], values=["Số lần tìm kiếm"], aggfunc='sum')
     piv2 = df_new2.pivot_table(index=["Keyword", "Tháng tìm kiếm nhiều nhất"], values=["Số lần tìm kiếm"], aggfunc='sum')
     writer = pd.ExcelWriter('vn_trending_top5_2019_2020.xlsx')
    
     df_new.to_excel(writer,sheet_name='Sheet1',index_label="STT", startcol = 0, startrow = 2)
     df_new2.to_excel(writer,sheet_name='Sheet1', startcol = 4, startrow = 2, index = False)

     worksheet = writer.sheets['Sheet1']
     workbook = writer.book
     center = workbook.add_format({'align': 'center'})
     cell_format = workbook.add_format({'size':15, 'align':'center'})

     worksheet.merge_range('A1:G1',"Danh sách từ khóa tìm kiếm tại Việt Nam",cell_format)
     worksheet.merge_range('A2:D2',"Năm 2020",cell_format)
     worksheet.merge_range('E2:G2',"Năm 2019",cell_format)
     print("Xuất báo cáo Top 10 trending 2019-2020 thành công !\n")
     writer.save()

def console():
          print("1. Lấy dữ liệu trending từ file.")
          print("2. Xuất báo cáo top 10 trending")
          print("3. Xuất báo cáo search keyword in 2020")
          print("4. Vẽ biểu đồ line chart top 5 trending các từ khóa tìm kiếm nhiều nhất 2020")
          print("5. Vẽ biểu đồ bar chart top 5 trending các từ khóa tìm kiếm nhiều nhất 2019")
          print("6. Thống kê tìm kiếm top trending 5 từ khóa trong 2 năm 2020, 2019")
          print("..................................")
          print("99. Thoát\n")

def clear():
     if platform.system() == 'Linux':
          os.system('clear')
     elif platform.system() == 'Windows':
          os.system('cls')
if __name__ == '__main__':
     clear()
     while True:
          console()
          you = input("Nhập lựa chọn: ")
          if you == "1":
               while you != f_name:
                    you = input("Nhập tên file:")
                    if you != f_name:
                         print("Tên file không tồn tại, hoặc không đúng định dạng")
               while True:
                    you = input("Nhập thời gian lấy dữ liệu theo định dạng yyyy-mm-dd: ")
                    if start_date <= you <= end_date:
                         date_check = you
                         input_data(f_name, date_check)
                         print("Successfully\n")
                         break
                    else:
                         print("Lỗi định dạng thời gian")
          elif you == "2":
               try:
                    top_10_trending()
               except Exception as err:
                    print("Error: ",err, "\n")
                    console()
          elif you == "3":
               try:
                    top_search_keyword_2020()
               except Exception as err:
                    print("Error: ",err, "\n")
                    console()             
          elif you == "4":
               try:
                    line_chart_top5_2020()
               except Exception as err:
                    print("Error: ",err, "\n")
                    console()
          elif you == "5":
               try:
                    bar_chart_top5_2019()
               except Exception as err:
                    print("Error: ",err, "\n")
                    console()
          elif you == "6":
               try:
                    top_10_trending_2020()
               except Exception as err:
                    print("Error: ",err, "\n")
                    console()
          elif you == "99":
            break
          else:
            print("***Vui lòng nhập lại***\n")
