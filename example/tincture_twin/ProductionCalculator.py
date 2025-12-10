import pandas as pd
import numpy as np
import os


class ProductionCalculator:
    def __init__(self, data_path):
        """
        Инициализация калькулятора производства.

        :param data_path: Путь к файлу с данными о движении товаров
        """
        self.data_path = data_path
        self.df = None
        self.last_date = None
        self.total_sales = None
        self.days_in_period = None
        self.ingredients_recipe = {'груши': 650, 'ананас': 125, 'водка': 500, 'конфеты': 100}
        self.load_and_prepare_data()  # Готовим данные сразу при инициализации

    def load_and_prepare_data(self):
        """
        Загружает и готовит данные для последующих расчетов.
        """
        # Читаем данные из CSV
        self.df = pd.read_csv(self.data_path)
        # Удаляем строки с пустыми датами
        self.df = self.df.dropna(subset=['Дата'])

    def calculate_average_daily_consumption(self):
        """
        Возвращает среднесуточный расход продукции.
        """
        # Используем подготовленные данные, не перегружаем их повторно
        self.last_date = self.df['Дата'].max()
        start_date = self.df['Дата'].min()
        filtered_df = self.df[self.df['Дата'] >= start_date]
        self.total_sales = filtered_df['Расход'].sum()
        self.days_in_period = len(filtered_df)

        # Проверка на случай нулевого периода
        if self.days_in_period > 0:
            avg_consumption = round(self.total_sales / self.days_in_period, 2)
        else:
            avg_consumption = 0
        return avg_consumption

    def calculate_forecasted_stock(self, forecast_days=7, weekend_factor=2):
        """
        Возвращает прогнозный запас на указанный период.

        :param forecast_days: Количество дней прогноза (по умолчанию 7)
        :param weekend_factor: Коэффициент увеличения прогноза на выходные (по умолчанию 2)
        """
        D_avg = self.calculate_average_daily_consumption()
        D_bar = round(D_avg * forecast_days, 2)
        D_bar *= weekend_factor
        return D_bar

    def calculate_safety_stock(self, forecast_days=7, safety_factor=0.12, weekend_factor=2):
        """
        Возвращает страховой запас.

        :param forecast_days: Количество дней прогноза (по умолчанию 7)
        :param safety_factor: Коэффициент страхового запаса (по умолчанию 0.12)
        :param weekend_factor: Коэффициент увеличения прогноза на выходные (по умолчанию 2)
        """
        D_bar = self.calculate_forecasted_stock(forecast_days, weekend_factor)
        S_min = round(safety_factor * D_bar, 2)
        return S_min

    def calculate_required_production(self, forecast_days=7, safety_factor=0.12, weekend_factor=2):
        """
        Возвращает необходимый объем производства.

        :param forecast_days: Количество дней прогноза (по умолчанию 7)
        :param safety_factor: Коэффициент страхового запаса (по умолчанию 0.12)
        :param weekend_factor: Коэффициент увеличения прогноза на выходные (по умолчанию 2)
        """
        D_bar = self.calculate_forecasted_stock(forecast_days, weekend_factor)
        S_min = self.calculate_safety_stock(forecast_days, safety_factor, weekend_factor)
        Vm = 2  # Минимальный объем производства
        rounded_P = int((D_bar + Vm - 1) // Vm) * Vm
        current_stock = self.df.iloc[-1]['Остаток']
        needed_production = rounded_P - current_stock

        if needed_production <= 0:
            final_P = round(Vm, 2)
        else:
            final_P = round(((needed_production + Vm - 1) // Vm) * Vm, 2)

        return final_P

    def calculate_ingredient_requirements(self, production_volume):
        """
        Возвращает список необходимых ингредиентов для указанного объема производства.

        :param production_volume: Объем производства в литрах
        """
        grapes_quantity = round(production_volume * self.ingredients_recipe['груши'], 2)
        pineapple_quantity = round(production_volume * self.ingredients_recipe['ананас'], 2)
        vodka_quantity = round(production_volume * self.ingredients_recipe['водка'], 2)
        candies_quantity = round(production_volume * self.ingredients_recipe['конфеты'], 2)

        return {
            'груши': grapes_quantity,
            'ананас': pineapple_quantity,
            'водка': vodka_quantity,
            'конфеты': candies_quantity
        }
