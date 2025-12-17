import flet as ft
import requests

AREA_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"

def main(page: ft.Page):
    page.title = "お天気マスター Pro + 気温表示"
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.window_width = 1100

    def get_weather_icons(weather_text):
        icons = []
        # ひらがな・漢字両方に対応
        if "晴" in weather_text or "はれ" in weather_text:
            icons.append(ft.Icon(ft.Icons.WB_SUNNY, color=ft.Colors.ORANGE, size=25))
        
        if len(icons) > 0 and any(x in weather_text for x in ["のち", "ときどき", "時々"]):
            if any(x in weather_text for x in ["曇", "くもり", "雨", "あめ", "雪", "ゆき"]):
                icons.append(ft.Icon(ft.Icons.ARROW_RIGHT_ALT, color=ft.Colors.GREY_400, size=20))

        if "曇" in weather_text or "くもり" in weather_text:
            icons.append(ft.Icon(ft.Icons.CLOUD, color=ft.Colors.BLUE_GREY_400, size=25))

        if "雨" in weather_text or "あめ" in weather_text:
            if len(icons) > 0 and icons[-1].name != ft.Icons.ARROW_RIGHT_ALT:
                if any(x in weather_text for x in ["のち", "ときどき", "時々"]):
                     icons.append(ft.Icon(ft.Icons.ARROW_RIGHT_ALT, color=ft.Colors.GREY_400, size=20))
            icons.append(ft.Icon(ft.Icons.UMBRELLA, color=ft.Colors.BLUE_600, size=25))

        if not icons:
            icons.append(ft.Icon(ft.Icons.QUESTION_MARK, color=ft.Colors.GREY_400, size=25))
        return icons

    # --- データ取得 ---
    area_raw = requests.get(AREA_URL).json()
    centers, offices = area_raw["centers"], area_raw["offices"]

    main_content = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=15)

    def on_area_click(e):
        area_code, area_name = e.control.data, e.control.title.value
        data_json = requests.get(FORECAST_URL.format(area_code)).json()
        
        main_content.controls.clear()
        main_content.controls.append(
            ft.Text(f"{area_name}の天気予報", style=ft.TextThemeStyle.HEADLINE_MEDIUM, weight="bold")
        )

        # 天気データ (index 0)
        weather_ts = data_json[0]["timeSeries"][0]
        weather_areas = weather_ts["areas"][0]
        
        # 気温データを探す (通常 index 2 に入っていることが多い)
        temp_data = []
        for ts in data_json[0]["timeSeries"]:
            if "temps" in ts["areas"][0]:
                temp_data = ts["areas"][0]["temps"]
                break

        for i in range(len(weather_areas["weathers"])):
            weather = weather_areas["weathers"][i]
            icons_list = get_weather_icons(weather)
            
            # 気温情報の作成
            temp_info = "気温情報なし"
            if len(temp_data) > i * 2 + 1:
                min_t = temp_data[i*2]
                max_t = temp_data[i*2 + 1]
                temp_info = f"最低 {min_t}℃ / 最高 {max_t}℃"
            elif len(temp_data) > i:
                temp_info = f"気温 {temp_data[i]}℃"

            main_content.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=15,
                        content=ft.ExpansionTile(
                            leading=ft.Row(icons_list, spacing=5, tight=True),
                            title=ft.Text(f"{weather_ts['timeDefines'][i][:10]}", size=18, weight="bold"),
                            subtitle=ft.Text(f"{weather}　{temp_info}", size=16),
                            controls=[
                                ft.ListTile(
                                    leading=ft.Icon(ft.Icons.THERMOSTAT, color=ft.Colors.RED_400),
                                    title=ft.Text("予想気温の詳細"),
                                    subtitle=ft.Text(temp_info),
                                ),
                                ft.ListTile(
                                    leading=ft.Icon(ft.Icons.AIR, color=ft.Colors.BLUE_GREY),
                                    title=ft.Text("風の予報"),
                                    subtitle=ft.Text(weather_areas["winds"][i])
                                )
                            ]
                        )
                    )
                )
            )
        page.update()

    # --- 左側メニュー ---
    area_menu = ft.Column(scroll=ft.ScrollMode.AUTO)
    for c_code, c_info in centers.items():
        state_tiles = [
            ft.ListTile(title=ft.Text(offices[ch]["name"]), on_click=on_area_click, data=ch)
            for ch in c_info["children"] if ch in offices
        ]
        area_menu.controls.append(ft.ExpansionTile(title=ft.Text(c_info["name"]), controls=state_tiles))

    page.add(
        ft.Row([
            ft.NavigationRail(destinations=[ft.NavigationRailDestination(icon=ft.Icons.WB_SUNNY, label="天気")], label_type="all"),
            ft.Container(content=area_menu, width=220, bgcolor=ft.Colors.WHITE),
            ft.Container(content=main_content, expand=True, padding=20)
        ], expand=True)
    )

ft.app(target=main)