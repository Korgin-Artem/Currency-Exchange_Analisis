import sqlite3
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import dash
from dash import html, dcc, Input, Output, State

def analysis_of_data(selected_values, selected_currency, start_date, end_date):
    graphs = []

    # Подключение к базе данных SQLite
    with sqlite3.connect('dataframe.db') as db:
        cursor = db.cursor()

        # Получение данных для выбранной валюты (selected_currency)
        cursor.execute(
            "SELECT exchange_rate, date FROM currency WHERE currency = ? AND date BETWEEN ? AND ? ORDER BY date",
            [selected_currency, start_date, end_date])
        selected_currency_data = cursor.fetchall()

        # Извлечение дат и цен для выбранной валюты
        selected_currency_dates = []
        selected_currency_prices = []
        for price, date in selected_currency_data:
            selected_currency_prices.append(price)
            selected_currency_dates.append(datetime.fromisoformat(date))

        # Создание графика для выбранной валюты
        selected_currency_fig = go.Figure([go.Scatter(x=selected_currency_dates, y=selected_currency_prices)])
        selected_currency_fig.update_layout(
            title=f'График курса {selected_currency}', xaxis_title='Дата', yaxis_title='Курс')
        graphs.append(dcc.Graph(figure=selected_currency_fig, config={'displayModeBar': False}))

        for currency in selected_values:
            if currency != selected_currency:
                # Получение данных для других валют
                cursor.execute(
                    "SELECT exchange_rate, date FROM currency WHERE currency = ? AND date BETWEEN ? AND ? ORDER BY date",
                    [currency, start_date, end_date])
                data_plot = cursor.fetchall()

                data_date = []
                data_price = []
                for price, date in data_plot:
                    data_price.append(price)
                    data_date.append(datetime.fromisoformat(date))

                # Рассчет относительных курсов для каждой выбранной валюты относительно selected_currency
                relative_prices = [price / selected_currency_prices[i] for i, price in enumerate(data_price)]

                # Создание графика с использованием Plotly для данных по валюте
                fig = go.Figure([go.Scatter(x=data_date, y=relative_prices)])
                fig.update_layout(
                    title=f'График курса {currency} относительно {selected_currency}', xaxis_title='Дата', yaxis_title='Курс')
                graphs.append(dcc.Graph(figure=fig, config={'displayModeBar': False}))

    return graphs

def choose_a_currency():
    # Загрузка доступных валют из файла Excel
    data_currency = pd.read_excel(
        f'Динамика официального курса заданной валюты с 01.07.1992 по 25.04.2023/1. Название валют.xlsx',
        index_col=None,
        header=None)

    available_currencies = [data_currency[0][i] for i in range(138)]

    # Создание приложения Dash
    app = dash.Dash(__name__, external_stylesheets=['styles.css'])

    app.layout = html.Div([
        html.Div(children=[
            html.Br(),
            html.Label('Выберите нужные валюты для анализа', className='label'),
            dcc.Dropdown(
                id='dropdown',
                options=[{'label': currency, 'value': currency}
                         for currency in available_currencies],
                placeholder="Выберите валюту",
                multi=True,
                value=[],
                className='currency-dropdown',
            ),
            dcc.DatePickerRange(
                id='date-range',
                start_date='2000-01-01',
                end_date='2022-12-31',
                display_format='YYYY-MM-DD',
                className='date-range'
            ),
            html.Button('Анализировать', id='analyze-button',
                        className='analyze-button'),
        ], className='currency-selector'),

        # Добавление второго выпадающего списка
        html.Div(children=[
            html.Br(),
            html.Label('Выберите вторую валюту', className='label'),
            dcc.Dropdown(
                id='second-dropdown',
                options=[{'label': currency, 'value': currency}
                         for currency in available_currencies],
                placeholder="Выберите вторую валюту",
                multi=False,
                value=None,
                className='currency-dropdown',
            ),
        ], className='currency-selector'),

        html.Div(id='graph-container', children=[], className='graph-container'),
    ])

    @app.callback(
        Output('graph-container', 'children'),
        Input('analyze-button', 'n_clicks'),
        State('dropdown', 'value'),
        State('second-dropdown', 'value'),  # Добавляем новый state
        State('date-range', 'start_date'),
        State('date-range', 'end_date')
    )
    def update_graphs(n_clicks, selected_values, selected_second_currency, start_date, end_date):
        if n_clicks is not None:
            graphs = analysis_of_data(selected_values, selected_second_currency, start_date, end_date)
            return graphs
        return []

    if __name__ == '__main__':
        app.run_server(debug=True)

if __name__ == '__main__':
    choose_a_currency()
