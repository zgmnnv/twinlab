import plotly.express as px
import pandas as pd
import dash
from dash import dcc, html


class VisualizationDashboard:
    def __init__(self, ingredients_needed, daily_avg_value, period_forecast_value, min_product_value):
        """
        Инициализация класса с необходимыми параметрами для визуализации.

        :param ingredients_needed: словарь с количеством ингредиентов
        :param daily_avg_value: среднесуточный расход продукта
        :param period_forecast_value: прогнозируемый запас
        :param min_product_value: минимальный запас
        """
        self.ingredients_needed = ingredients_needed
        self.daily_avg_value = daily_avg_value
        self.period_forecast_value = period_forecast_value
        self.min_product_value = min_product_value
        self.app = None

    def create_dataframes(self):
        """Создание DataFrames для двух типов данных."""
        df_ingredients = pd.DataFrame({
            'Ингредиент': list(self.ingredients_needed.keys()),
            'Количество': list(self.ingredients_needed.values())
        })

        df_values = pd.DataFrame({
            'Показатель': ['Среднесуточный расход', 'Прогнозный запас', 'Минимальный запас'],
            'Значение': [self.daily_avg_value, self.period_forecast_value, self.min_product_value]
        })
        return df_ingredients, df_values

    def build_graphs(self):
        """Строит графики на основе созданных ранее DataFrames."""
        df_ingredients, df_values = self.create_dataframes()

        fig1 = px.bar(df_ingredients, x='Ингредиент', y='Количество',
                      title='Запасы ингредиентов',
                      color_discrete_sequence=['indianred'])
        fig1.update_layout(title_text='Необходимые запасы ингредиентов', xaxis_title='Ингредиент',
                           yaxis_title='Количество (гр./мл.)')

        fig2 = px.bar(df_values, x='Показатель', y='Значение',
                      title='Структура запасов и потребления',
                      color_discrete_sequence=["gold"])
        fig2.update_layout(title_text='Анализ запасов и потребностей', xaxis_title='Тип показателя',
                           yaxis_title='Объем (литры)')

        return fig1, fig2

    def create_dashboard(self):
        """Инициализирует объект приложения и создает структуру страницы."""
        if self.app is None:
            self.app = dash.Dash(__name__)

        fig1, fig2 = self.build_graphs()

        self.app.layout = html.Div([
            html.H1(children='Dashboard производственного плана'),
            dcc.Graph(id='graph1', figure=fig1),
            dcc.Graph(id='graph2', figure=fig2)
        ], style={'width': '100%', 'display': 'inline-block'})

    def run_app(self, debug=False):
        """Запускает приложение на локальном сервере."""
        if self.app is None:
            self.create_dashboard()
        self.app.run(debug=debug)