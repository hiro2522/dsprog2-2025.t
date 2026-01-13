import flet as ft
import requests
import sqlite3
from datetime import datetime

# --- 定数 ---
AREA_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"
DB_NAME = "weather_database.db"

# --- データベース管理クラス ---
class WeatherDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        self.init_tables()

    def init_tables(self):
        cur = self.conn.cursor()
        # エリア情報テーブル
        cur.execute("CREATE TABLE IF NOT EXISTS areas (code TEXT PRIMARY KEY, name TEXT)")
        # 予報データテーブル (created_atで履歴を管理)
        cur.execute('''CREATE TABLE IF NOT EXISTS forecasts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        area_code TEXT,
                        forecast_date TEXT,
                        weather TEXT,
                        wind TEXT,
                        temp_min TEXT,
                        temp_max TEXT,
                        created_at TEXT)''')
        self.conn.commit()

    def save_data(self, area_code, area_name, forecasts):
        cur = self.conn.cursor()
        # エリア情報の保存
        cur.execute("INSERT OR REPLACE INTO areas VALUES (?, ?)", (area_code, area_name))
        # 予報データの保存
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for f in forecasts:
            cur.execute('''INSERT INTO forecasts (area_code, forecast_date, weather, wind, temp_min, temp_max, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (area_code, f['date'], f['weather'], f['wind'], f['min'], f['max'], now))
        self.conn.commit()

    def get_latest(self, area_code):
        """特定のエリアの最新取得分（3日分）を取得"""
        cur = self.conn.cursor()
        cur.execute('''SELECT * FROM forecasts WHERE area_code = ? 
                       ORDER BY created_at DESC LIMIT 3''', (area_code,))
        return cur.fetchall()

    def get_by_date(self, area_code, date_str):
        """特定の日付の予報を履歴から検索"""
        cur = self.conn.cursor()
        cur.execute('''SELECT * FROM forecasts WHERE area_code = ? AND forecast_date = ? 
                       ORDER BY created_at DESC''', (area_code, date_str))
        return cur.fetchall()

# DBインスタンスの生成
db = WeatherDB()

def main(page: ft.Page):
    page.title = "お天気マスター Pro + SQLite Storage"
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.window_width = 1100

    # 状態管理用
    selected_area_code = ft.Ref[str]()

    def get_weather_icons(weather_text):
        icons = []
        if "晴" in weather_text or "はれ" in weather_text:
            icons.append(ft.Icon(ft.Icons.WB_SUNNY, color=ft.Colors.ORANGE, size=25))
        if "曇" in weather_text or "くもり" in weather_text:
            icons.append(ft.Icon(ft.Icons.CLOUD, color=ft.Colors.BLUE_GREY_400, size=25))
        if "雨" in weather_text or "あめ" in weather_text:
            icons.append(ft.Icon(ft.Icons.UMBRELLA, color=ft.Colors.BLUE_600, size=25))
        return icons if icons else [ft.Icon(ft.Icons.QUESTION_MARK, color=ft.Colors.GREY_400)]

    main_content = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=15)

    def render_view(area_code, area_name, date_filter=None):
        """DBからデータを読み取って表示を更新する共通関数"""
        main_content.controls.clear()
        
        # データの取得（日付指定があるか否か）
        if date_filter:
            rows = db.get_by_date(area_code, date_filter)
            title = f"{area_name} の予報履歴 ({date_filter})"
        else:
            rows = db.get_latest(area_code)
            title = f"{area_name} の最新予報 (DB)"

        main_content.controls.append(ft.Text(title, style=ft.TextThemeStyle.HEADLINE_MEDIUM, weight="bold"))

        if not rows:
            main_content.controls.append(ft.Text("データが見つかりません。地域を選び直してください。"))
        else:
            for r in rows:
                # row[3]:天気, row[2]:日付, row[5]:最低, row[6]:最高, row[4]:風, row[7]:取得時
                icons = get_weather_icons(r[3])
                temp_info = f"最低 {r[5]}℃ / 最高 {r[6]}℃"
                main_content.controls.append(
                    ft.Card(ft.Container(padding=15, content=ft.ExpansionTile(
                        leading=ft.Row(icons, spacing=5, tight=True),
                        title=ft.Text(f"{r[2]}", size=18, weight="bold"),
                        subtitle=ft.Text(f"{r[3]}　{temp_info}"),
                        controls=[
                            ft.ListTile(title=ft.Text("風の予報"), subtitle=ft.Text(r[4])),
                            ft.ListTile(title=ft.Text("取得日時"), subtitle=ft.Text(r[7]), text_color="grey")
                        ]
                    )))
                )
        page.update()

    def on_area_click(e):
        area_code, area_name = e.control.data, e.control.title.value
        selected_area_code.current = area_code
        
        # 1. APIから最新データを取得
        try:
            res = requests.get(FORECAST_URL.format(area_code)).json()
            
            # 2. JSONを解析してDB用データを作成
            weather_ts = res[0]["timeSeries"][0]
            temp_data = []
            for ts in res[0]["timeSeries"]:
                if "temps" in ts["areas"][0]:
                    temp_data = ts["areas"][0]["temps"]
                    break
            
            forecast_list = []
            for i in range(len(weather_ts["areas"][0]["weathers"])):
                min_t = temp_data[i*2] if len(temp_data) > i*2 else "-"
                max_t = temp_data[i*2+1] if len(temp_data) > i*2+1 else "-"
                forecast_list.append({
                    "date": weather_ts["timeDefines"][i][:10],
                    "weather": weather_ts["areas"][0]["weathers"][i],
                    "wind": weather_ts["areas"][0]["winds"][i],
                    "min": min_t, "max": max_t
                })
            
            # 3. DBに保存（ここでJSONからDBへ移行完了）
            db.save_data(area_code, area_name, forecast_list)
            
        except Exception as ex:
            print(f"Fetch Error: {ex}")

        # 4. 表示（常にDBから読み出す）
        render_view(area_code, area_name)

    # 日付選択（オプション機能）
    def on_date_change(e):
        if selected_area_code.current:
            date_str = e.control.value.strftime("%Y-%m-%d")
            render_view(selected_area_code.current, "履歴検索", date_filter=date_str)

    datepicker = ft.DatePicker(on_change=on_date_change)
    page.overlay.append(datepicker)

    # --- UI構築 ---
    area_raw = requests.get(AREA_URL).json()
    area_menu = ft.Column(scroll=ft.ScrollMode.AUTO)
    for c_code, c_info in area_raw["centers"].items():
        state_tiles = [
            ft.ListTile(title=ft.Text(area_raw["offices"][ch]["name"]), on_click=on_area_click, data=ch)
            for ch in c_info["children"] if ch in area_raw["offices"]
        ]
        area_menu.controls.append(ft.ExpansionTile(title=ft.Text(c_info["name"]), controls=state_tiles))

    page.add(
        ft.Row([
            ft.NavigationRail(
                destinations=[ft.NavigationRailDestination(icon=ft.Icons.WB_SUNNY, label="天気")],
                label_type="all"
            ),
            ft.Container(
                content=ft.Column([
                    ft.ElevatedButton("日付で履歴を検索", icon=ft.Icons.EVENT, on_click=lambda _: datepicker.pick_date()),
                    ft.Divider(),
                    area_menu
                ]), width=220, bgcolor=ft.Colors.WHITE, padding=10
            ),
            ft.Container(content=main_content, expand=True, padding=20)
        ], expand=True)
    )

ft.app(target=main)