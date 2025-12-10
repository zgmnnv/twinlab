import paho.mqtt.client as mqtt
import json
import os


class DigitalTwinPublisher:
    def __init__(self, config_file):
        """
        Инициализация MQTT клиента и подключение к брокеру.

        :param config_file: Путь к файлу с параметрами цифрового двойника
        """
        # Загружаем параметры из файла
        with open(config_file, 'r') as f:
            params = json.load(f)

        self.namespace = params["namespace"]
        self.main_twin_name = params["main_twin_name"]
        self.ingredient_names = params["ingredient_names"]
        self.forecast_names = params["forecast_names"]
        self.broker = params["mqtt_broker"]
        self.port = params["mqtt_port"]
        self.username = params["mqtt_username"]
        self.password = params["mqtt_password"]
        self.topic_prefix = "telemetry/"  # Префикс темы MQTT

        # Настройки клиента MQTT
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.username_pw_set(self.username, self.password)
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc, properties=None):
        """
        Callback при подключении к MQTT брокеру.
        """
        if rc == 0:
            print("Successfully connected to MQTT broker")
        else:
            print(f"Connection failed with code {rc}")

    def on_publish(self, client, userdata, mid, reason_code, properties):
        """
        Callback при успешной публикации сообщения.
        """
        print(f"Message {mid} published successfully with reason code: {reason_code}")

    def disconnect(self):
        """
        Завершает соединение с MQTT брокером.
        """
        self.client.loop_stop()
        self.client.disconnect()
        print("Disconnected from MQTT broker")

    def send_data_to_ditto(self, grapes_quantity, vodka_quantity, candies_quantity, pineapple_quantity, d_avg, s_min,
                           d_bar, final_p):
        """
        Генерирует и публикует данные в MQTT брокер для цифрового двойника.

        :param grapes_quantity: Вес груш
        :param vodka_quantity: Кол-во водки
        :param candies_quantity: Вес конфет
        :param pineapple_quantity: Вес ананаса
        :param d_avg: Среднесуточный расход
        :param s_min: Страховой запас
        :param d_bar: Прогнозный запас
        :param final_p: Итоговый объем производства
        """
        # Формируем протокол для ингредиентов
        for idx, ingredient_name in enumerate(self.ingredient_names):
            value = locals()[list(['grapes_quantity', 'vodka_quantity', 'candies_quantity', 'pineapple_quantity'])[idx]]
            payload = self.get_ditto_protocol_value_tincture_ingredient(value)
            message = self.get_ditto_protocol_msg(ingredient_name, payload)
            full_topic = f"{self.topic_prefix}{self.namespace}/{ingredient_name}"
            print(f"Publishing {ingredient_name}: {value} → {full_topic}")
            self.client.publish(full_topic, json.dumps(message))

        # Формируем протокол для прогнозов
        forecasts = [
            ("Средний расход в день", d_avg),
            ("Прогнозный запас", d_bar),
            ("Страховой запас", s_min),
            ("Итоговый объем производства", final_p)
        ]
        for idx, (desc, val) in enumerate(forecasts):
            forecast_name = self.forecast_names[idx]
            payload = self.get_ditto_protocol_value_tincture_forecast(val)
            message = self.get_ditto_protocol_msg(forecast_name, payload)
            full_topic = f"{self.topic_prefix}{self.namespace}/{forecast_name}"
            print(f"Publishing {desc}: {val} → {full_topic}")
            self.client.publish(full_topic, json.dumps(message))

        # Формируем общий протокол для главного цифрового двойника
        msg_protocol = self.get_ditto_protocol_value_tincture(grapes_quantity, vodka_quantity, candies_quantity,
                                                              pineapple_quantity, d_avg, s_min, d_bar, final_p)
        message = self.get_ditto_protocol_msg(self.main_twin_name, msg_protocol)
        full_topic = f"{self.topic_prefix}{self.namespace}/{self.main_twin_name}"
        print(f"Publishing {self.main_twin_name} → {full_topic}")
        self.client.publish(full_topic, json.dumps(message))

    def get_ditto_protocol_value_tincture(self, grapes_quantity, vodka_quantity, candies_quantity, pineapple_quantity,
                                          d_avg, s_min, d_bar, final_p):
        """
        Формирует JSON-запись для отправки в цифровой двойник (продукт).
        """
        return {
            "ingredient_forecast": {
                "properties": {
                    "grape": grapes_quantity,
                    "vodka": vodka_quantity,
                    "candies": candies_quantity,
                    "pineapple": pineapple_quantity
                }
            },
            "product_forecast": {
                "properties": {
                    "d_avg": d_avg,
                    "s_min": s_min,
                    "d_bar": d_bar,
                    "final_p": final_p
                }
            }
        }

    def get_ditto_protocol_value_tincture_ingredient(self, value):
        """
        Формирует JSON-запись для отправки данных ингредиента.
        """
        return {
            "Value": {
                "properties": {
                    "value": value
                }
            }
        }

    def get_ditto_protocol_value_tincture_forecast(self, value):
        """
        Формирует JSON-запись для отправки данных прогноза.
        """
        return {
            "forecast_value": {
                "properties": {
                    "value": value
                }
            }
        }

    def get_ditto_protocol_msg(self, name, value):
        """
        Формирует общее сообщение для отправки в MQTT брокер.
        """
        return {
            "topic": f"{self.namespace}/{name}/things/twin/commands/merge",
            "headers": {
                "content-type": "application/merge-patch+json"
            },
            "path": "/features",
            "value": value
        }