import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
from folium import FeatureGroup
from update_data import get_data
from models_back import Link, BankBranch

class DataLoader:
    def __init__(self, currency: Link):
        self.currency = currency
        self.target_currency = self._get_currency_code_from_link(currency)

    def load_data(self) -> pd.DataFrame:
        branches = get_data(self.currency)
        return self._convert_to_dataframe(branches)

    def _get_currency_code_from_link(self, link: Link) -> str:
        """Извлекает код валюты из Link enum"""
        return link.name

    def _convert_to_dataframe(self, branches: list[BankBranch]) -> pd.DataFrame:
        records = []
        for branch in branches:
            record = {
                "branch_id": branch.id,
                "bank_name": branch.bank_org.name,
                "address": branch.address,
                "lon": branch.coords.lon,
                "lat": branch.coords.lat,
                "buy_course": None,
                "sell_course": None,
            }
            for rate in branch.exchange_rates:
                # Ищем курсы BYN->TARGET и TARGET->BYN
                if rate.curr_from.value == "byn" and rate.curr_to.value == self.target_currency.lower():
                    record["buy_course"] = float(rate.rate)
                elif rate.curr_from.value == self.target_currency.lower() and rate.curr_to.value == "byn":
                    record["sell_course"] = float(rate.rate)
            records.append(record)

        df = pd.DataFrame(records)
        if df["buy_course"].isna().all():
            raise ValueError(f"No buy_course (BYN->{self.target_currency}) rates found.")
        return df.dropna(subset=["buy_course"])

class DataProcessor:
    @staticmethod
    def compute_weight(df: pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy()
        df_copy["weight_raw"] = 1 / df_copy["buy_course"]
        min_w, max_w = df_copy["weight_raw"].min(), df_copy["weight_raw"].max()
        df_copy["weight"] = (df_copy["weight_raw"] - min_w) / (max_w - min_w + 1e-6)
        df_copy["weight"] = df_copy["weight"] ** 2.5
        return df_copy

    @staticmethod
    def get_color(course: float, min_c: float, max_c: float) -> str:
        norm = (course - min_c) / (max_c - min_c + 1e-6)
        norm = norm ** 2
        if norm < 0.33: return "green"
        elif norm < 0.66: return "orange"
        return "red"

class MapBuilder:
    def __init__(self, center: tuple, zoom: int):
        self.center = center
        self.zoom = zoom
        self.map = folium.Map(location=center, zoom_start=zoom, tiles='OpenStreetMap')
        self.best_rates_group = FeatureGroup(name='Лучшие курсы', show=True)
        self.best_rates_group.add_to(self.map)

    def add_heatmap(self, df: pd.DataFrame) -> "MapBuilder":
        heat_data = df[["lat", "lon", "weight"]].values.tolist()
        HeatMap(heat_data, radius=20, blur=15, min_opacity=0.3, max_zoom=18).add_to(self.map)
        return self

    def add_markers(self, df: pd.DataFrame) -> "MapBuilder":
        cluster = MarkerCluster(
            disableClusteringAtZoom=15, spiderfyOnMaxZoom=True,
            zoomToBoundsOnClick=True, showCoverageOnHover=False
        ).add_to(self.map)
        
        min_c = df["buy_course"].min()
        max_c = df["buy_course"].max()
        
        for _, row in df.iterrows():
            color = DataProcessor.get_color(row["buy_course"], min_c, max_c)
            popup = self._create_popup(row)
            folium.CircleMarker(
                location=[row["lat"], row["lon"]], radius=8, color=color,
                fill=True, fill_opacity=0.88, weight=2,
                popup=folium.Popup(popup, max_width=300),
            ).add_to(cluster)
        return self

    def add_best_rate_marker(self, df: pd.DataFrame) -> "MapBuilder":
        if df.empty:
            return self

        try:
            if df["buy_course"].isna().all():
                print(f"[WARNING] Нет данных buy_course для маркера лучшей покупки")
                return self

            best_buy = df.loc[df["buy_course"].idxmin()]
            popup_buy = f"★ <b>ЛУЧШАЯ ПОКУПКА</b><br><b>{best_buy['bank_name']}</b><br>Курс: {best_buy['buy_course']}<br>{best_buy['address']}"
            folium.Marker(
                location=[best_buy["lat"], best_buy["lon"]],
                icon=folium.Icon(color="green", icon="star", prefix="fa"),
                popup=popup_buy
            ).add_to(self.best_rates_group)
        except Exception as e:
            print(f"[WARNING] Ошибка добавления маркера лучшей покупки: {e}")

        try:
            if not df["sell_course"].isna().all():
                best_sell = df.loc[df["sell_course"].idxmax()]
                popup_sell = f"★ <b>ЛУЧШАЯ ПРОДАЖА</b><br><b>{best_sell['bank_name']}</b><br>Курс: {best_sell['sell_course']}<br>{best_sell['address']}"
                folium.Marker(
                    location=[best_sell["lat"], best_sell["lon"]],
                    icon=folium.Icon(color="blue", icon="star", prefix="fa"),
                    popup=popup_sell
                ).add_to(self.best_rates_group)
        except Exception as e:
            print(f"[WARNING] Ошибка добавления маркера лучшей продажи: {e}")

        return self

    @staticmethod
    def _create_popup(row) -> str:
        return f"""
        <b>{row['bank_name']}</b><br>
        <b>{row['address']}</b><br>
        Курс покупки: {row['buy_course']}<br>
        Курс продажи: {row['sell_course']}<br>
        """

class ExchangeMap:
    def __init__(self, currency: Link = Link.USD, 
                 city_center: tuple = (53.904, 27.5616), 
                 zoom: int = 12):
        self.currency = currency
        self.city_center = city_center
        self.zoom = zoom
        self.df = None
        self.data_loader = DataLoader(self.currency)
        self.map_builder = MapBuilder(city_center, zoom)

    def build(self) -> "ExchangeMap":
        self.df = self.data_loader.load_data()
        print(f"[DEBUG] Построение карты для {self.currency.name}. Строк в датафрейме: {len(self.df)}")
        print(f"[DEBUG] Столбцы с NaN - buy_course: {self.df['buy_course'].isna().sum()}, sell_course: {self.df['sell_course'].isna().sum()}")
        if not self.df.empty:
            print(f"[DEBUG] Min buy_course: {self.df['buy_course'].min()}, Max: {self.df['buy_course'].max()}")
        self.df = DataProcessor.compute_weight(self.df)
        self.map_builder.add_heatmap(self.df)
        self.map_builder.add_markers(self.df)
        print(f"[DEBUG] Добавляю маркер лучшей покупки для {self.currency.name}")
        self.map_builder.add_best_rate_marker(self.df)
        return self

    def get_html(self) -> str:
        """Возвращает HTML-код карты как строку для вставки в шаблон Flask"""
        return self.map_builder.map.get_root().render()

    def save_and_open(self, filename: str = "generated_heatmap.html") -> None:
        """Оставляем для локальных тестов"""
        import webbrowser, os
        self.map_builder.map.save(filename)
        try:
            webbrowser.open('file://' + os.path.realpath(filename))
        except Exception as e:
            print(f"[WARNING] Не удалось открыть браузер: {e}")