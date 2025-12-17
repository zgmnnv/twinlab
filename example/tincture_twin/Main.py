from TableManager import TableManager
from ProductionCalculator import ProductionCalculator
from DigitalTwinPublisher import DigitalTwinPublisher
from VisualizationDashboard import VisualizationDashboard

#Обрабатываем таблицу и сохраняем результат
tm = TableManager()

input_table_path = 'table/product_movement_data.csv'
output_table_path = 'table/processed_product_movement_data.csv'
tm.preprocess_and_save(input_table_path, output_table_path)

#Проводим расчеты прогноза по объему производства и ингридиентам
pc = ProductionCalculator(output_table_path)

# Период прогноза
forecast_days = 7
# Коэфициент умножения для расчета продаж в выходные
weekend_factor = 3
# Минимальный коэфициент для запаса товара от общего объема продаж за период
safety_factor = 0.2

pc.load_and_prepare_data()
daily_avg_value = pc.calculate_average_daily_consumption()
period_forecast_value = pc.calculate_forecasted_stock(forecast_days, weekend_factor)
min_product_value = pc.calculate_safety_stock(forecast_days, safety_factor, weekend_factor)
required_production_value = pc.calculate_required_production(forecast_days, safety_factor, weekend_factor)
ingredients_needed = pc.calculate_ingredient_requirements(required_production_value)

#Передаем полученные данные в ЦД
config_file = "digital_twin_parameters.json"
publisher = DigitalTwinPublisher(config_file)

publisher.send_data_to_ditto(
    ingredients_needed['груши'], ingredients_needed['ингредиент V'], ingredients_needed['конфеты'], ingredients_needed['ананас'],
    daily_avg_value, min_product_value, period_forecast_value, required_production_value)

publisher.disconnect()

#Рисуем дашборд с итогами
vd = VisualizationDashboard(ingredients_needed, daily_avg_value, period_forecast_value, min_product_value)
vd.run_app()


# Публикуем в консоль прогнозы
print(f"Среднесуточный расход: {daily_avg_value:.2f} литров/день")
print(f"Прогнозный запас: {period_forecast_value:.2f} литров")
print(f"Минимальный запас: {min_product_value:.2f} литров")
print(f"Необходимое производство: {required_production_value:.2f} литров")

print("\nИнгредиенты:")
for ingredient, quantity in ingredients_needed.items():
    print(f"{ingredient}: {quantity} граммов/миллилитров")
