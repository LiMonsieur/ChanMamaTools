# 作者：Limonsieur
# 时间：2023/7/15 13:00
# 说明：鱼为蛙打造的工具包
# encoding: utf-8

import tkinter as tk
from tkinter import ttk
from tkinter.constants import *
import configparser
import requests
import json
import hashlib
import time
import datetime
import pandas as pd
import logging
import urllib.request
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),  # 控制台处理器
        logging.FileHandler('Frog.log')  # 文件处理器
    ]
)

# 通用浏览器请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Origin": "https://www.chanmama.com",
    "Referer": "https://www.chanmama.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "X-Client-Id": "1481251155",
}


# 当前时间的10位时间戳
def get_timestamp():
    timestamp = int(time.time())
    return timestamp


# md5加密
def get_md5(string):
    m = hashlib.md5()
    m.update(string.encode("utf8"))
    return m.hexdigest()


def get_token(username, passwd):
    url = "https://api-service.chanmama.com/v1/access/token"
    passwd = get_md5(passwd)
    data = {
        "username": username,
        "password": passwd,
        "timestamp": get_timestamp(),
        "appId": 10000,
        "from_platform": "web",
    }
    response = requests.post(url, data=json.dumps(data))
    try:
        if json.loads(response.text)["data"]["logged_in"]:
            logging.info("小鲤鱼向蛙蛙报告！登录成功啦！")
            headers["Cookie"] = response.headers["set-cookie"]
            user_token = json.loads(response.text)["data"]["token"]
            return user_token
    except Exception as e:
        logging.error("报告蛙蛙长官！登录失败")
        logging.error(f"失败原因：{e}")
        logging.error("大事不妙惹，小鲤鱼要跑路了！")
        # 退出程序
        exit(0)


# 获取搜索人物信息
def get_person_detail(keyword):
    url = "https://api-service.chanmama.com/v5/home/author/search"
    request_data = {
        "keyword": keyword,
    }
    response = requests.get(url, headers=headers, params=request_data, timeout=20)
    # 再次按照服务器要修修改Cookie
    headers["Cookie"] = headers["Cookie"] + f";{response.headers['Set-Cookie']}"
    response = json.loads(response.text)
    total_count = response["data"]["page_info"]["totalCount"]

    person_search_list = response["data"]["list"] or response["data"]["dy_authors"]
    total_count = max(total_count, len(person_search_list))
    logging.info("报告蛙蛙长官！")
    logging.info(f"《{keyword}》共找到{total_count}个结果！")
    rank_first = person_search_list[0]
    result_data = {"name": rank_first["nickname"],
                   "author_id": rank_first["author_id"],  # 人物ID，下一步检索使用
                   "avatar": rank_first["avatar"],  # 头像
                   "label": rank_first["label"],  # 标签
                   "unique_id": rank_first["unique_id"],  # 抖音号
                   "follower_count": rank_first["follower_count"],  # 粉丝数
                   "follower_incr": rank_first["follower_incr"],  # 粉丝增长数
                   # "live_count_30:": rank_first["live_count_30"],  # 30天直播数
                   # "live_average_amount_30": rank_first["live_average_amount_30"],  # 30天直播平均销售额
                   # "live_average_user_30": rank_first["live_average_user_30"],  # 30天直播平均观看人数
                   }
    return result_data


def get_live_history(anchor_id, days=7):
    url = "https://api-service.chanmama.com/v1/author/detail/room"
    # 查询日期范围7天
    start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    logging.info("报告蛙蛙长官！")
    logging.info(f"查询日期范围：{start_date}至{end_date}")

    request_data = {
        "author_id": anchor_id,
        "page": 1,
        "size": 100,
        "start_date": start_date,
        "end_date": end_date,
    }
    response = requests.get(url, headers=headers, params=request_data, timeout=20)
    response = json.loads(response.text)
    history_list = response["data"]["list"]
    return [{"begin_time": x["begin_time"],
             "room_finish_time": x["room_finish_time"],
             "room_id": x["room_id"],
             "room_title": x["room_title"],
             } for x in history_list]


def get_live_room_detail(live_room_id):
    url = "https://api-service.chanmama.com/v1/douyin/live/room/info"
    request_data = {
        "room_id": live_room_id,
    }
    response = requests.get(url, headers=headers, params=request_data, timeout=20)
    response = json.loads(response.text)
    live_room_detail = response["data"]["room"]
    live_room_detail_data = {"room_id": live_room_id,
                             "room_title": live_room_detail["room_title"],
                             "like_count": live_room_detail["like_count"],  # 点赞数
                             "average_user_count": live_room_detail["average_user_count"],  # 平均在线
                             "average_residence_time": live_room_detail["average_residence_time"],  # 平均观看时长
                             "total_user": live_room_detail["total_user"],  # 总观看人数
                             "watch_cnt": live_room_detail["watch_cnt"],  # 累计观看次数
                             "convert_fan_rate": live_room_detail["convert_fan_rate"],  # 粉丝转化率
                             "interaction_percent": live_room_detail["interaction_percent"],  # 互动率
                             "user_peak": live_room_detail["user_peak"],  # 最高在线
                             "barrage_count": live_room_detail["barrage_count"],  # 弹幕数
                             "increment_follower_count": live_room_detail["increment_follower_count"],  # 新增粉丝数

                             }
    return live_room_detail_data


# 时间戳转日期
def timestamp_to_date(timestamp):
    time_local = time.localtime(timestamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", time_local)


# 秒数转时分秒
def second_to_hms(second):
    m, s = divmod(second, 60)
    h, m = divmod(m, 60)
    if h == 0:
        if m == 0:
            return "%02d秒" % s
        return "%02d分%02d秒" % (m, s)

    return "%02d时%02d分%02d秒" % (h, m, s)


# 配置文件类
class Config:
    def __init__(self):
        self.path = r'./config.ini'
        self.config = configparser.ConfigParser()
        self.config.read(self.path, encoding='gbk')

    def get(self, section, key):
        return self.config.get(section, key)

    def set(self, section, key, value):
        try:
            self.config.set(section, key, value)
        except configparser.NoSectionError:
            self.config.add_section(section)
            self.config.set(section, key, value)
        with open(self.path, 'w') as f:
            self.config.write(f)


# 蛙蛙工具包窗体
class Tool:
    # 初始化窗体
    def __init__(self, title, width=300, height=700):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(width=False, height=False)
        # self.root.iconbitmap("frog.ico")

        label = tk.Label(self.root, highlightbackground="white", highlightthickness=0)
        label.pack()
        # 添加两个按钮
        self.live_button = tk.Button(self.root, text="抖音主播数据", command=self.live_button_click)
        self.live_button.place(relx=0.5, rely=0.1, anchor=tk.CENTER)

        self.user_info_button = tk.Button(self.root, text="留资用户信息", command=self.user_info_button_click)
        self.user_info_button.place(relx=0.5, rely=0.3, anchor=tk.CENTER)

        #  添加一个文本框，用于显示结果
        self.result_text = tk.Text(self.root, width=40, height=20, wrap=tk.WORD)
        self.result_text.place(relx=0.5, rely=0.7, anchor=tk.CENTER)

    def live_button_click(self):
        LiveWindow("抖音主播数据")
        self.root.destroy()

    def user_info_button_click(self):
        RetainWindow("留资用户信息")
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# 抖音主播数据窗体
class LiveWindow:
    def __init__(self, title, width=300, height=700):
        self.query_button = None
        self.anchorId = None
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(width=False, height=False)
        # self.root.iconbitmap("frog.ico")

        # # 添加菜单栏，退出、关于和返回主窗口界面
        # self.menu_bar = tk.Menu(self.root)
        # self.root.config(menu=self.menu_bar)
        # self.main_menu = tk.Menu(self.menu_bar, tearoff=False)
        # self.main_menu.add_cascade(label="返回主窗口", command=self.back_to_main)
        #
        # self.main_menu.add_cascade(label="退出", command=self.root.quit)
        # self.root.config(menu=self.menu_bar)

        #  添加一个文本框，用于显示结果
        self.result_text = tk.Text(self.root, width=40, height=20, wrap=tk.WORD)
        self.result_text.grid(row=0, column=0, columnspan=2, sticky=NSEW)
        self.result_text.pack(side=BOTTOM, fill=X, padx=10, pady=10)

        # 添加一个下拉菜单选择查询范围
        # 添加下拉框说明
        self.period_label = tk.Label(self.root, text="请选择查询时间范围：")
        self.period_label.pack()

        self.comBoxList = ttk.Combobox(self.root, width=20)
        self.comBoxList["values"] = (1, 3, 7, 15, 30)
        self.comBoxList.current(0)
        self.comBoxList.bind("<<ComboboxSelected>>")
        self.daysRange = self.comBoxList.get()

        self.comBoxList.pack()
        # 添加一个输入框，用于输入主播ID
        self.label = tk.Label(self.root, text="请输入主播名称或者ID：")
        self.label.pack()

        # 读取配置文件
        self.config = Config()
        self.anchor = tk.Entry(self.root, width=20)
        # 从配置文件中读取上次输入的主播ID
        try:
            search_list = self.config.get("search_anchor", "anchor_id")
            if search_list == "":
                self.anchor.insert(0, "主播一,主播二,主播三,英文逗号分隔")
            else:
                self.anchor.insert(0, search_list)
        except configparser.Error as e:
            print(e)
            self.config.set("search_anchor", "anchor_id", "")
            self.anchor.insert(0, "主播一,主播二,主播三")
        self.anchor.bind("<Double-Button-1>", lambda event: self.anchor.delete(0, END))
        # 单击时要是存在查询按钮则删除
        self.anchor.bind("<Button-1>", lambda event: self.query_button.destroy())

        self.anchor.pack(fill=X, padx=10, pady=10)

        self.checkButton = tk.Button(self.root, text="检查输入主播格式", command=self.checkAnchor)
        self.checkButton.pack()
        self.tips_label = tk.Label(self.root, text="注意：多个主播ID请用英文逗号分隔\n"
                                                   "双击清空输入框", fg="blue")
        self.tips_label.pack()

        try:
            self.login_username = self.config.get("login_user", "username")
            self.result_text.insert(tk.END, f"检查到本地保存的蝉妈妈用户名为\n"
                                            f"{self.login_username}\n")
            self.login_password = self.config.get("login_user", "password")
        except configparser.Error as e:
            print(e)
            self.chanMama_label = tk.Label(self.root, text="检查到本地无蝉妈妈登陆信息\n请先保存蝉妈妈用户名和密码",
                                           fg="red")
            self.chanMama_label.pack()
            # 弹出一个窗口提示用户输入用户名和密码
            self.login_username_window = tk.Entry(self.root, width=20)
            self.login_username_window.insert(0, "请输入蝉妈妈用户名")
            self.login_username_window.bind("<Button-1>", lambda event: self.login_username_window.delete(0, END))
            self.login_username_window.pack(fill=X, padx=10, pady=10)

            self.login_password_window = tk.Entry(self.root, width=20)
            self.login_password_window.insert(0, "请输入蝉妈妈密码")
            self.login_password_window.bind("<Button-1>", lambda event: self.login_password_window.delete(0, END))
            self.login_password_window.pack(fill=X, padx=10, pady=10)

            # 添加一个按钮，用于保存用户名和密码
            self.save_button = tk.Button(self.root, text="保存蝉妈妈用户名和密码", command=self.save_button_click)
            self.save_button.pack(fill=X, padx=10, pady=10)

    def back_to_main(self):
        self.root.destroy()
        Tool("蛙蛙工具包").run()

    def save_button_click(self):
        self.config.set("login_user", "username", self.login_username_window.get())
        self.config.set("login_user", "password", self.login_password_window.get())
        self.login_username = self.login_username_window.get()
        self.login_password = self.login_password_window.get()
        # 清空用户名密码文本框和按钮
        self.login_username_window.destroy()
        self.login_password_window.destroy()
        self.save_button.destroy()
        self.chanMama_label.destroy()

    def checkAnchor(self):
        self.anchorId = self.anchor.get()
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "检查主播ID:\n")
        self.result_text.insert(tk.END, "-------------------\n")
        if self.anchorId == "" or self.anchorId is None:
            self.result_text.insert(tk.END, "主播ID不能为空，请输入主播ID！\n")
        else:
            for x in self.anchorId.split(","):
                self.result_text.insert(tk.END, f"{x}\n")

            self.result_text.insert(tk.END, "-------------------\n")
            self.result_text.insert(tk.END, "检查完成。\n")
            self.result_text.insert(tk.END, "确认无误后点击查询按钮即可开始。\n")
            # 保存输入的主播ID
            self.config.set("search_anchor", "anchor_id", self.anchorId)

            # 添加一个按钮，用于查询
            # 查看当前是否已经存在查询按钮，如果存在则先删除
            if self.query_button is not None:
                self.query_button.destroy()

            self.query_button = tk.Button(self.root, text="查询", command=self.query_button_click)
            self.query_button.pack(side=BOTTOM, fill=X, padx=10, pady=10)

    def query_button_click(self):
        # 清空文本框
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "查询抖音主播数据\n")
        self.daysRange = self.comBoxList.get()
        self.result_text.insert(tk.END, f"当前查询范围{self.daysRange}天的数据。\n")
        self.anchorId = self.anchor.get()
        if self.anchorId == "" or self.anchorId is None:
            self.result_text.insert(tk.END, "主播ID不能为空，请输入主播ID！\n")
        else:
            self.result_text.insert(tk.END, f"当前查询主播ID为{self.anchorId}。\n")
            try:
                token = get_token(self.login_username, self.login_password)
            except AttributeError:
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, "报告蛙蛙长官！小鲤鱼检查到您还没有保存蝉妈妈用户名和密码！\n")
                self.result_text.insert(tk.END, "请先保存蝉妈妈用户名和密码！\n")
                self.result_text.insert(tk.END, "保存完成后再次点击查询按钮即可开始查询！\n")
                self.result_text.insert(tk.END, "求求你啦~\n")
                self.query_button.destroy()
                return
            if token:
                self.result_text.insert(tk.END, "报告蛙蛙长官！小鲤鱼已经登录蝉妈妈啦！\n")
                self.result_text.insert(tk.END, "报告蛙蛙长官！小鲤鱼正在查询主播信息！\n")
            else:
                self.result_text.insert(tk.END, "报告蛙蛙长官！小鲤鱼登录蝉妈妈失败！\n")
                time.sleep(3)
                self.result_text.insert(tk.END, "这可咋整啊！\n")
                time.sleep(3)
                self.result_text.insert(tk.END, "小鲤鱼要跑路了！\n")
                time.sleep(3)
                self.result_text.insert(tk.END, "蛙蛙长官，我先走了！\n")
                time.sleep(3)
                self.result_text.insert(tk.END, "3s中后程序自动退出！\n")
                time.sleep(3)
                exit(0)
            search_list = self.anchorId.split(",")
            for anchor in search_list:
                self.result_text.insert(tk.END, f"报告蛙蛙长官！小鲤鱼正在扒{anchor}的直播小秘密！\n")
                person_data = get_person_detail(anchor)
                # avatar_bytes = urlopen(person_data['avatar']).read()
                # data_stream = io.BytesIO(avatar_bytes)
                # pil_image = Image.open(data_stream)
                # tk_image = ImageTk.PhotoImage(pil_image)
                # self.result_text.image_create(tk.END, image=tk_image)
                # self.result_text.insert(tk.END, "\n")

                author_id = person_data["author_id"]
                self.result_text.insert(tk.END, f"人物名称：{person_data['name']}\n"
                                                f"人物ID：{person_data['author_id']}\n"
                # f"人物头像：{person_data['avatar']}\n"
                                                f"人物标签：{person_data['label']}\n"
                                                f"抖音号：{person_data['unique_id']}\n"
                                                f"粉丝数：{person_data['follower_count']}\n"
                                                f"粉丝增长数：{person_data['follower_incr']}\n")

                live_history_range = int(self.daysRange)
                live_history_list = get_live_history(author_id, live_history_range)
                if len(live_history_list) == 0:
                    logging.info(f"这家伙最近{live_history_range}天没有直播记录！\n")
                    self.result_text.insert(tk.END, f"这家伙最近{live_history_range}天没有直播记录！\n")
                else:
                    logging.info(f"这家伙最近{live_history_range}天的直播记录我都找到了！\n"
                                 f"一共{len(live_history_list)}条，\n"
                                 f"您请看！\n")
                    self.result_text.insert(tk.END, f"这家伙最近{live_history_range}天的直播记录我都找到了！\n"
                                                    f"一共{len(live_history_list)}条，\n"
                                                    f"您请看！\n")

                    # 生成一个直播间的pandas表格，循环结束之后保存为一个sheet页
                    live_history_df = pd.DataFrame(
                        columns=[
                            "开播时间",
                            "直播时长",
                            "曝光人数",
                            "场观",
                            "曝光观看率",
                            "最高在线人数",
                            "平均在线人数",
                            "平均观看时长",
                            "关注率",
                            "互动率",

                        ])

                    for live_history in live_history_list:
                        room_id = live_history["room_id"]
                        room_detail = get_live_room_detail(room_id)
                        logging.info(
                            f"直播间标题：{room_detail['room_title']}\n"
                            f"直播间ID：{room_detail['room_id']}\n"
                            f"开始时间：{timestamp_to_date(live_history['begin_time'])}\n"
                            f"结束时间：{timestamp_to_date(live_history['room_finish_time'])}\n"
                            f"直播时长：{second_to_hms(int((live_history['room_finish_time'] - live_history['begin_time'])))}\n"
                            f"点赞数：{room_detail['like_count']}\n"
                            f"平均在线：{room_detail['average_user_count']}\n"
                            f"平均观看时长：{second_to_hms(room_detail['average_residence_time'])}\n"
                            f"总观看人数：{room_detail['total_user']}\n"
                            f"累计观看次数：{room_detail['watch_cnt']}\n"
                            f"粉丝转化率：{room_detail['convert_fan_rate']}\n"
                            f"互动率：{room_detail['interaction_percent']}\n"
                            f"最高在线：{room_detail['user_peak']}\n"
                            f"弹幕数：{room_detail['barrage_count']}\n"
                            f"新增粉丝数：{room_detail['increment_follower_count']}\n")
                        self.result_text.insert(tk.END,
                                                f"直播间标题：{room_detail['room_title']}\n"
                                                f"直播间ID：{room_detail['room_id']}\n"
                                                f"开始时间：{timestamp_to_date(live_history['begin_time'])}\n"
                                                f"结束时间：{timestamp_to_date(live_history['room_finish_time'])}\n"
                                                f"直播时长：{second_to_hms(int((live_history['room_finish_time'] - live_history['begin_time'])))}\n"
                                                f"点赞数：{room_detail['like_count']}\n"
                                                f"平均在线：{room_detail['average_user_count']}\n"
                                                f"平均观看时长：{second_to_hms(room_detail['average_residence_time'])}\n"
                                                f"总观看人数：{room_detail['total_user']}\n"
                                                f"累计观看次数：{room_detail['watch_cnt']}\n"
                                                f"粉丝转化率：{room_detail['convert_fan_rate']}\n"
                                                f"互动率：{room_detail['interaction_percent']}\n"
                                                f"最高在线：{room_detail['user_peak']}\n"
                                                f"弹幕数：{room_detail['barrage_count']}\n"
                                                f"新增粉丝数：{room_detail['increment_follower_count']}\n")

                        live_history_df = live_history_df.append(
                            {
                                "开播时间": timestamp_to_date(live_history['begin_time']),
                                "直播时长": second_to_hms(int((live_history['room_finish_time'] - live_history[
                                    'begin_time']))),
                                "曝光人数": "",
                                "场观": room_detail['total_user'],
                                "曝光观看率": "",
                                "最高在线人数": room_detail['user_peak'],
                                "平均在线人数": room_detail['average_user_count'],
                                "平均观看时长": second_to_hms(room_detail['average_residence_time']),
                                "关注率": str(room_detail['convert_fan_rate']) + "%",
                                "互动率": str(room_detail['interaction_percent']) + "%",

                            }, ignore_index=True)

                        time.sleep(1)
                    # # 保存为excel
                    try:
                        with pd.ExcelWriter(f"抖音主播数据{datetime.datetime.now().strftime('%Y-%m-%d')}.xlsx",
                                            engine='openpyxl',
                                            mode='a') as writer:
                            # 设置index从1开始
                            live_history_df.index = live_history_df.index + 1
                            live_history_df.to_excel(writer, sheet_name=f"直播信息-{person_data['name']}",
                                                     index=False)
                    except FileNotFoundError:
                        with pd.ExcelWriter(f"抖音主播数据{datetime.datetime.now().strftime('%Y-%m-%d')}.xlsx",
                                            engine='openpyxl',
                                            mode='w') as NewFileWriter:
                            live_history_df.index = live_history_df.index + 1
                            live_history_df.to_excel(NewFileWriter, sheet_name=f"直播信息-{person_data['name']}",
                                                     index=False)

                    logging.info(f"报告蛙蛙长官！信息已保存为excel文件！\n"
                                 f"蛙蛙长官，我已经完成了我的任务！\n"
                                 f"小的先告辞了！\n")
                    self.result_text.insert(tk.END, f"报告蛙蛙长官！信息已保存为excel文件！\n"
                                                    f"请蛙蛙长官查收！\n")


# 留资用户信息窗体
class RetainWindow:
    def __init__(self, title, width=300, height=700):
        self.download_button = None
        self.query_button = None
        self.anchorId = None
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(width=False, height=False)
        # self.root.iconbitmap("frog.ico")

        #  添加一个文本框，用于显示结果
        self.result_text = tk.Text(self.root, width=40, height=20, wrap=tk.WORD)
        self.result_text.grid(row=0, column=0, columnspan=2, sticky=NSEW)
        self.result_text.pack(side=BOTTOM, fill=X, padx=10, pady=10)

        today = datetime.datetime.now().strftime("%Y-%m-%d")

        # 添加开始时间和结束时间选择控件
        self.start_date_label = tk.Label(self.root, text="请输入开始时间：")
        self.start_date_label.pack()
        self.start_date = tk.Entry(self.root, width=20)
        self.start_date.insert(0, today)
        # 双击时清空输入框
        self.start_date.bind("<Double-Button-1>", lambda event: self.start_date.delete(0, END))
        self.start_date.pack(fill=X, padx=10, pady=10)

        self.end_date_label = tk.Label(self.root, text="请输入结束时间：")
        self.end_date_label.pack()
        self.end_date = tk.Entry(self.root, width=20)
        self.end_date.insert(0, today)
        self.end_date.bind("<Double-Button-1>", lambda event: self.end_date.delete(0, END))
        self.end_date.pack(fill=X, padx=10, pady=10)

        self.warn_mes = tk.Label(self.root, text="注意：时间格式为YYYY-MM-DD\n"
                                                 "双击清空输入框\n"
                                                 "为空默认为查询所有时间范围。", fg="blue")
        self.warn_mes.pack()

        self.config = Config()
        self.author = tk.Entry(self.root, width=20)
        self.admin_phone_label = tk.Label(self.root, text="请输入管理员手机号：")
        self.admin_phone_label.pack()
        # 从配置文件中读取上次输入的管理员手机号
        try:
            phone = self.config.get("admin", "phone")
            if phone == "":
                self.author.insert(0, "输入管理员手机号")
            else:
                self.author.insert(0, phone)
        except configparser.Error as e:
            print(e)
            self.config.set("admin", "phone", "")
            self.author.insert(0, "输入管理员手机号")
        self.author.bind("<Double-Button-1>", lambda event: self.author.delete(0, END))
        # 单击时要是存在查询按钮则删除
        self.author.pack(fill=X, padx=10, pady=10)
        self.query_button = tk.Button(self.root, text="查询", command=self.query_button_click)
        self.query_button.pack(side=BOTTOM, fill=X, padx=10, pady=10)

    def query_button_click(self):
        # 删除多余的download_button
        if self.download_button is not None:
            self.download_button.destroy()
        start_date = self.start_date.get()
        end_date = self.end_date.get()
        phone = self.author.get()

        if phone == "" or phone is None:
            self.result_text.insert(tk.END, "管理员手机号不能为空，请输入管理员手机号！\n")
        else:
            try:
                phone = int(phone)
            except ValueError:
                # 清空文本框
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, "管理员手机号格式不正确，请重新输入！\n")
                return
            # 清空文本框
            self.result_text.delete(1.0, tk.END)
            # 保存输入的管理员手机号
            self.config.set("admin", "phone", str(phone))
            self.result_text.insert(tk.END, f"开始时间：{start_date}\n"
                                            f"结束时间：{end_date}\n"
                                            f"管理员手机号：{phone}\n")

            try:
                download_url = self.getUserInfoDownload(start_date, end_date, phone)
            except Exception as e:
                self.result_text.insert(tk.END, f"报告蛙蛙长官！小鲤鱼查询失败！\n"
                                                f"错误信息：{e}\n")
                return

            # 下载按钮
            self.download_button = tk.Button(self.root, text="下载",
                                             command=lambda: self.download_button_click(download_url))
            self.download_button.pack(side=BOTTOM, fill=X, padx=10, pady=10)
            self.result_text.insert(tk.END, f"报告蛙蛙长官！小鲤鱼查询成功！\n"
                                            f"下载链接：{download_url}\n"
                                            f"请点击下载按钮下载！\n")

    def download_button_click(self, download_url):
        if download_url is None:
            self.result_text.insert(tk.END, f"报告蛙蛙长官！小鲤鱼还没有查询到下载链接！\n"
                                            f"请稍后再试！\n")
        else:
            self.result_text.insert(tk.END, f"报告蛙蛙长官！小鲤鱼正在下载文件！\n"
                                            f"请稍后！\n")
            try:
                # file_name = download_url.split("/")[-1]
                file_path = os.path.join(os.getcwd(), "用户信息.xlsx")
                urllib.request.urlretrieve(download_url, file_path)
                self.result_text.insert(tk.END, f"报告蛙蛙长官！小鲤鱼下载成功！\n"
                                                f"文件保存在{file_path}\n")
            except Exception as e:
                self.result_text.insert(tk.END, f"报告蛙蛙长官！小鲤鱼下载失败！\n"
                                                f"错误信息：{e}\n")

    @staticmethod
    def getUserInfoDownload(start_date, end_date, phone):
        url = "https://servicestrong-hrb.com/frog/api/frogDownload"
        # url = "http://127.0.0.1:8000/api/frogDownload"
        request_data = {
            "start_date": start_date,
            "end_date": end_date,
            "phone": phone,
        }
        response = requests.get(url, params=request_data, timeout=20)
        response = json.loads(response.text)
        if response["status"]:
            download_url = response["message"]
        else:
            download_url = None
        return download_url


if __name__ == '__main__':
    tool = Tool("鱼为蛙打造的工具包")
    tool.run()
