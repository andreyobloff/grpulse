# GreenPulse — разработка и тестирование API

## Практическая работа №29

Документ описывает REST API проекта GreenPulse и порядок его тестирования.

В исходном задании для TaskManager требовалось реализовать создание, получение и удаление задач. В проекте GreenPulse аналогичная логика адаптирована к предметной области экологического мониторинга: реализованы операции создания, получения и удаления записей экологических измерений.

## 1. Назначение API

API предназначен для взаимодействия внешних приложений с GreenPulse.

Через API внешняя система может:

- создать новую запись экологического измерения;
- получить список всех записей;
- удалить запись по идентификатору;
- проверить корректность API-ключа;
- получить ошибку при некорректном запросе.

## 2. Реализованные эндпоинты

| Метод | URL | Назначение |
|---|---|---|
| `POST` | `/api/readings` | Создание новой записи измерения |
| `GET` | `/api/readings` | Получение всех записей измерений |
| `DELETE` | `/api/readings/{id}` | Удаление записи измерения по ID |

## 3. Авторизация

Для доступа к API используется простой API-ключ.

Ключ передается в заголовке:

```http
X-API-Key: greenpulse-demo-key
```

Если ключ отсутствует или указан неверно, API возвращает статус:

```text
401 Unauthorized
```

## 4. Формат данных

API использует JSON.

### 4.1. Создание записи

Запрос:

```http
POST /api/readings
Content-Type: application/json
X-API-Key: greenpulse-demo-key
```

Тело запроса:

```json
{
  "record_id": "REC-API-001",
  "station_id": "MSK-001",
  "district": "ЦАО",
  "sensor_type": "pm25",
  "value": 18.4,
  "measured_at": "2026-05-25T12:00:00"
}
```

Успешный ответ:

```json
{
  "message": "reading created",
  "reading": {
    "record_id": "REC-API-001",
    "station_id": "MSK-001",
    "district": "ЦАО",
    "sensor_type": "pm25",
    "value": 18.4,
    "measured_at": "2026-05-25T12:00:00"
  }
}
```

Код ответа: `201 Created`.

### 4.2. Получение списка записей

Запрос:

```http
GET /api/readings
X-API-Key: greenpulse-demo-key
```

Успешный ответ:

```json
{
  "count": 1,
  "readings": [
    {
      "record_id": "REC-API-001",
      "station_id": "MSK-001",
      "district": "ЦАО",
      "sensor_type": "pm25",
      "value": 18.4,
      "measured_at": "2026-05-25T12:00:00"
    }
  ]
}
```

Код ответа: `200 OK`.

### 4.3. Удаление записи

Запрос:

```http
DELETE /api/readings/REC-API-001
X-API-Key: greenpulse-demo-key
```

Успешный ответ:

```json
{
  "message": "reading deleted",
  "record_id": "REC-API-001"
}
```

Код ответа: `200 OK`.

## 5. Ошибочные запросы

| Ситуация | Код | Ответ |
|---|---|---|
| Не указан API-ключ | `401` | `invalid or missing api key` |
| Передан неверный API-ключ | `401` | `invalid or missing api key` |
| Не указан обязательный параметр | `400` | `missing field: <field>` |
| Неизвестный тип датчика | `400` | `unknown sensor type` |
| Некорректное значение | `400` | `value must be a number` |
| Запись не найдена при удалении | `404` | `reading not found` |
| Неизвестный endpoint | `404` | `endpoint not found` |

## 6. Примеры тестирования через curl

### 6.1. Запуск API

```bash
python -m src.api
```

По умолчанию API запускается по адресу:

```text
http://127.0.0.1:8000
```

### 6.2. Создание записи

```bash
curl -X POST http://127.0.0.1:8000/api/readings \
  -H "Content-Type: application/json" \
  -H "X-API-Key: greenpulse-demo-key" \
  -d '{
    "record_id": "REC-API-001",
    "station_id": "MSK-001",
    "district": "ЦАО",
    "sensor_type": "pm25",
    "value": 18.4
  }'
```

### 6.3. Получение записей

```bash
curl -X GET http://127.0.0.1:8000/api/readings \
  -H "X-API-Key: greenpulse-demo-key"
```

### 6.4. Удаление записи

```bash
curl -X DELETE http://127.0.0.1:8000/api/readings/REC-API-001 \
  -H "X-API-Key: greenpulse-demo-key"
```

### 6.5. Проверка ошибочного запроса

```bash
curl -X GET http://127.0.0.1:8000/api/readings
```

Ожидаемый результат: `401 Unauthorized`.

## 7. Автоматическое тестирование API

Для API добавлен файл:

```text
tests/test_api.py
```

Проверяются сценарии:

- успешное создание записи;
- успешное получение списка записей;
- успешное удаление записи;
- отказ при отсутствии API-ключа;
- отказ при некорректном payload;
- ответ `404` при удалении несуществующей записи.

Запуск тестов:

```bash
PYTHONPATH=. python -m tests.test_api
```

## 8. CI/CD

Для автоматической проверки API добавлен workflow:

```text
.github/workflows/api_tests.yml
```

Workflow запускается при push, pull request и вручную через GitHub Actions.

## 9. Файлы, добавленные в рамках ПЗ29

| Файл | Назначение |
|---|---|
| `src/api.py` | REST API GreenPulse |
| `tests/test_api.py` | Автоматические тесты API |
| `.github/workflows/api_tests.yml` | GitHub Actions workflow для API |
| `docs/api/API_TESTING_GreenPulse.md` | Документация по API и тестированию |

## 10. Ссылки

- Репозиторий: https://github.com/andreyobloff/grpulse
- Документация API: https://github.com/andreyobloff/grpulse/blob/main/docs/api/API_TESTING_GreenPulse.md
- API-код: https://github.com/andreyobloff/grpulse/blob/main/src/api.py
- API-тесты: https://github.com/andreyobloff/grpulse/blob/main/tests/test_api.py
- GitHub Actions: https://github.com/andreyobloff/grpulse/actions
