# PowerShell-скрипты для работы с Kafka (de-hw06)

Набор скриптов "создать топик → записать → прочитать → удалить" для Kafka, поднятой в docker
(сервис `broker` из `hw06\docker-compose.yaml`, образ `apache/kafka:4.3.1`).

Все Kafka-команды выполняются внутри контейнера через `docker exec broker ...` с
`--bootstrap-server localhost:29092` (INTERNAL-листенер). На хосте Kafka-бинарники не нужны —
только Docker Desktop.

Каждый скрипт пишет логи **и в консоль (цветные), и в файл** `scripts\logs\<имя>-yyyyMMdd-HHmmss.log`
(один файл на запуск). Скрипты совместимы с Windows PowerShell 5.1 и PowerShell 7+.

## Требования

- Инфраструктура поднята и брокер здоров:
  ```powershell
  docker compose up -d
  docker inspect --format "{{.State.Health.Status}}" broker
  ```
- Если ExecutionPolicy блокирует запуск скриптов:
  ```powershell
  Set-ExecutionPolicy -Scope Process Bypass
  ```
  либо запускайте с явным флагом: `powershell -NoProfile -ExecutionPolicy Bypass -File <скрипт>`.

## Состав

| Скрипт                    | Назначение                                                                                                                                                     |
|---------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `common.ps1`              | Общая библиотека (dot-source'ится остальными скриптами): логирование, вызовы Kafka CLI через `docker exec`, preflight-проверки. Самостоятельно не запускается. |
| `01-create-topic.ps1`     | Создаёт топик (идемпотентно: если топик уже есть - WARN и пропуск) и выводит `--describe` (партиции, RF, ISR).                                                 |
| `02-produce-messages.ps1` | Записывает в топик N JSON-сообщений одним вызовом `kafka-console-producer.sh`. Возвращает RunId последней строкой stdout.                                      |
| `03-consume-messages.ps1` | Читает сообщения через `kafka-console-consumer.sh` (с timestamp/partition/offset), считает общее число и число сообщений заданного RunId.                      |
| `04-delete-topic.ps1`     | Удаляет топик (идемпотентно). Без `-Force` запрашивает подтверждение (нужно ввести имя топика).                                                                |
| `run-all.ps1`             | Полный сценарий: `01` → `02` → `03` в отдельных процессах, с одним общим лог-файлом и одним общим RunId. Останавливается на первом упавшем шаге.               |
| `logs\`                   | Создаётся автоматически; `*.log` исключён из git (`.gitignore`).                                                                                               |

## Общие параметры (есть у всех скриптов 01–04)

| Параметр           | По умолчанию      | Описание                                                                              |
|--------------------|-------------------|---------------------------------------------------------------------------------------|
| `-Topic`           | `test`            | Имя топика Kafka.                                                                     |
| `-ContainerName`   | `broker`          | Имя docker-контейнера с Kafka.                                                        |
| `-BootstrapServer` | `localhost:29092` | Bootstrap-адрес **внутри контейнера**.                                                |
| `-KafkaBin`        | `/opt/kafka/bin`  | Каталог Kafka CLI в контейнере (при отсутствии скрипт сам найдёт его через PATH).     |
| `-LogFile`         | (создаётся новый) | Путь к лог-файлу. Используется `run-all.ps1`, чтобы все шаги писали в один общий лог. |

## Запуск

Из каталога `hw06`:

### run-all.ps1 - весь сценарий целиком

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-all.ps1
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts\run-all.ps1 -Topic test -Count 5
```

| Параметр                                                         | По умолчанию     | Описание                                                                                                                     |
|------------------------------------------------------------------|------------------|------------------------------------------------------------------------------------------------------------------------------|
| `-Topic`                                                         | `test`           | Топик для всех шагов.                                                                                                        |
| `-Count`                                                         | `5`              | Сколько сообщений произвести (шаг 02).                                                                                       |
| `-RunId`                                                         | `yyyyMMddHHmmss` | Общий идентификатор прогона; добавляется в payload каждого сообщения и используется шагом 03 для подсчёта "своих" сообщений. |
| `-MaxMessages`                                                   | `Count + 500`    | Лимит чтения шага 03 (запас нужен, чтобы прочитать и сообщения прошлых прогонов).                                            |
| `-TimeoutMs`                                                     | `15000`          | Таймаут консьюмера (мс).                                                                                                     |
| `-ContainerName` / `-BootstrapServer` / `-KafkaBin` / `-LogFile` | см. выше         | Прокидываются во все шаги.                                                                                                   |

Exit code: `0` - SUCCESS, `1` - FAILED (остановка на первом упавшем шаге). В конце печатается
итоговая строка с длительностью и путём к общему логу.

### 01-create-topic.ps1 - создание топика

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\01-create-topic.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\01-create-topic.ps1 -Topic test -Partitions 3 -ReplicationFactor 1
```

| Параметр             | По умолчанию | Описание                                                         |
|----------------------|--------------|------------------------------------------------------------------|
| `-Topic`             | `test`       | Имя создаваемого топика.                                         |
| `-Partitions`        | `3`          | Число партиций (1–1000).                                         |
| `-ReplicationFactor` | `1`          | Фактор репликации (1–10; для одно-брокерного кластера только 1). |

Поведение: если топик уже существует - WARN, создание пропускается, затем выполняется
`--describe`. Exit code `0/1`.

### 02-produce-messages.ps1 - запись сообщений

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\02-produce-messages.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\02-produce-messages.ps1 -Count 3 -RunId my-run-1
```

| Параметр    | По умолчанию     | Описание                                                                        |
|-------------|------------------|---------------------------------------------------------------------------------|
| `-Topic`    | `test`           | Топик назначения (должен существовать, иначе ERROR и подсказка запустить `01`). |
| `-Count`    | `5`              | Число сообщений (1–100000).                                                     |
| `-RunId`    | `yyyyMMddHHmmss` | Идентификатор прогона, включается в JSON каждого сообщения.                     |
| `-Messages` | (нет)            | Массив строк для отправки вместо автогенерации JSON (переопределяет `-Count`).  |

Формат сообщения по умолчанию (ASCII, одна строка = одно сообщение, без ключа):

```json
{"id":1,"runId":"20260927153643","event":"user_login","source":"ps-script","seq":1,"ts":"2026-09-27T12:36:43Z"}
```

Последняя строка stdout - RunId (используется при конвейерных вызовах). Exit code `0/1`.

### 03-consume-messages.ps1 - чтение сообщений

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\03-consume-messages.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\03-consume-messages.ps1 -MaxMessages 10 -TimeoutMs 10000 -RunId my-run-1
```

| Параметр         | По умолчанию | Описание                                                               |
|------------------|--------------|------------------------------------------------------------------------|
| `-Topic`         | `test`       | Топик для чтения.                                                      |
| `-MaxMessages`   | `100`        | Остановиться после N сообщений.                                        |
| `-TimeoutMs`     | `15000`      | Таймаут консьюмера в мс (1–600000).                                    |
| `-RunId`         | (нет)        | Если задан - дополнительно считает прочитанные сообщения с этим RunId. |
| `-FromBeginning` | `$true`      | Читать с начала топика (`$false` - только новые сообщения).            |

Каждая строка выводится в формате `CreateTime:... Partition:... Offset:... <payload>`.
Особенность Kafka 4.x: при срабатывании `--timeout-ms` консьюмер печатает `TimeoutException`,
но если есть итоговая строка `Processed a total of N messages`, шаг считается успешным
(WARN в логе, exit `0`). Без итоговой строки - ERROR, exit `1`.

### 04-delete-topic.ps1 - удаление топика

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\04-delete-topic.ps1            # с подтверждением
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\04-delete-topic.ps1 -Force     # без подтверждения
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\04-delete-topic.ps1 -Topic test -Force
```

| Параметр | По умолчанию | Описание                                                                                                                             |
|----------|--------------|--------------------------------------------------------------------------------------------------------------------------------------|
| `-Topic` | `test`       | Удаляемый топик.                                                                                                                     |
| `-Force` | (не задан)   | Пропустить интерактивное подтверждение. Без него скрипт попросит ввести имя топика; при несовпадении удаление отменяется (exit `1`). |

Идемпотентно: если топика нет - WARN и exit `0`. После `--delete` скрипт до 5 секунд ждёт
исчезновения топика из `--list`; если топик ещё помечен как удаляемый - WARN (не ошибка).

**Осторожно:** удаление безвозвратно стирает все сообщения топика.

## Логи

- Файлы: `scripts\logs\<скрипт>-yyyyMMdd-HHmmss.log`, формат строки:
  `2026-09-27 16:22:01.978 [INFO ] [01-create-topic] сообщение` (уровни: `INFO`, `STEP`, `WARN`, `ERROR`).
- `run-all.ps1` передаёт свой лог-файл детям через `-LogFile`, поэтому весь сценарий
  (все шаги) оказывается в одном файле.
- В git логи не попадают (`*.log` в `.gitignore`).

## Проверка результата

- Kafka UI: http://localhost:8080 → кластер `local` → топик `test` → Messages.
- Grafana: http://localhost:3000 (admin/admin) — трафик появится на дашборде.
