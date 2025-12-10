import pandas as pd
import os


class TableManager:

    def preprocess_and_save(self, input_path, output_path):

        os.chdir('/Users/zgmnnv/Dev/TwinLab')
        try:
            # Читаем исходный CSV-файл
            df = pd.read_csv(input_path)

            # Удаляем строки с пустыми значениями в столбце 'Дата'
            df = df.dropna(subset=['Дата'])

            # Конвертируем столбец 'Дата' в формат datetime
            df['Дата'] = pd.to_datetime(df['Дата'], format='%d.%m.%Y', errors='coerce')

            # Чистим и конвертируем числовые столбцы
            df['Приход'] = df['Приход'].fillna(0).astype(int)
            df['Расход'] = df['Расход'].fillna(0).astype(int)
            df['Остаток'] = df['Остаток'].fillna(0).astype(int)

            # Преобразуем значения из миллилитров в литры
            df['Приход'] /= 1000
            df['Расход'] /= 1000
            df['Остаток'] /= 1000

            # Информация о типах данных и общих характеристиках
            print("Типы данных:")
            print(df.dtypes)
            print("\nОбщая информация о данных:")
            df.info()

            # Сохраняем обработанные данные в новый CSV-файл
            df.to_csv(output_path, index=False)
            print(f"\nИзмененные данные сохранены в {output_path}!")

        except Exception as e:
            print(f"Произошла ошибка: {e}")
