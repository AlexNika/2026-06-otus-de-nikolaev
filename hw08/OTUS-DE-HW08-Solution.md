# OTUS DE-2026-06, HW08 - Витрина данных по преступлениям Бостона

Основная реализация витрины - PySpark (`pyspark_solution/`). Для верификации результата она продублирована на 
Java 21 (`java_solution/`). Паритет обеих версий подтверждён скриптом tools/compare_marts.py.
Оба решения работают на одном Spark 4.2.0 standalone-кластере (master + 2 воркера) из **одного** Docker-образа,
читают одни и те же `hw08/data/crime.csv` и `hw08/data/offense_codes.csv` и пишут результат в
`hw08/data/output/pyspark` и `hw08/data/output/java`. Результаты обеих реализаций совпадают по содержимому - это 
подтверждено скриптом `tools/compare_marts.py` (`PARITY OK: 12 districts, 0 differences`).

Почему я сделал 2 реализации? Задание допускало одну реализацию, однако паритет двух независимых реализаций одной и 
той же логики - это форма `differential testing`: она подтверждает и корректность гексоганальной архитектуры 
(порты/адаптеры переносятся между языками без изменений), и эквивалентность результата. В продакшене вместо второй 
реализации обычно используют `golden dataset` с фиксированным ожидаемым выводом - это дешевле в поддержке. 
В рамках учебного задания вторая реализация выбрана сознательно, т.к. она даёт более сильную проверку, 
чем единственный эталон.

У данного подхода есть и ограничения. Паритет подтверждает эквивалентность двух реализаций, но не абсолютную 
корректность витрины: согласованная ошибка в обеих версиях не будет обнаружена. 
Проверка корректности - отдельная задача, решаемая `golden dataset` или независимым источником истины.

Приложение очищает данные, соединяет их по коду правонарушения и считает по районам (district) метрики:
`crimes_total`, `crimes_monthly` (медиана преступлений в месяц), `frequent_crime_types`
(топ-3 типа преступления через запятую по убыванию частоты), `lat`, `lng` (средние координаты).
Витрина сохраняется одним parquet-файлом (`coalesce(1)`).

---

## Сравнение решений и выбор

| Критерий | Java (`java_solution/`) | PySpark (`pyspark_solution/`) |
|---|---|---|
| Язык и типизация | Java 21, статическая типизация, compile-time проверки | Python 3, динамическая типизация + type hints |
| Артефакт | shaded jar (`maven-shade-plugin`) | скрипт + пакет исходников |
| Доставка в образ | multi-stage: сборка jar в стадии `maven`, затем `COPY --from=build` | обычный `COPY` исходников |
| CLI | позиционные аргументы (`AppConfig.fromArgs`) | argparse-флаги (`--crimes_path` и т.д.) |
| Логирование | slf4j + log4j2 | модуль `logging` |
| DI / сборка зависимостей | `AppContext.java` | `context.py` |
| Объём кода | ~431 строка, 22 файла (`src/**/*.java`) | ~313 строк, 12 файлов (`boston_crimes_mart*/**/*.py`) |
| Скорость итерации | правка → `mvn package` → jar → запуск | правка → запуск (без этапа сборки) |
| Порог входа | выше (Maven, экосистема JVM) | ниже |

Архитектура обоих решений одинакова: гексагональная архитектура - порты/адаптеры, DI-контекст, pipeline из шагов
load → clean → enrich → aggregate → write. Порядок агрегаторов совпадает, поэтому порядок
колонок в витрине одинаков: `district, crimes_total, lat, lng, crimes_monthly, frequent_crime_types`.

**Основная реализация - PySpark**, аргументы выбора:

- Python - основной язык DE-экосистемы (Airflow, dbt, pandas/polars, MLlib): один язык на весь пайплайн;
- итерации без этапа компиляции и сборки jar - изменение сразу попадает в задачу;
- меньше бойлерплейта при той же SOLID-архитектуре (порты, адаптеры, DI-контекст);
- нативная работа в notebook'ах (исследование данных, прототипирование);
- совместимость с managed-сервисами (Dataproc, EMR, Glue, Databricks), где Python-джобы - first-class citizen;
- в нашей витрине нет кастомных User-Defined Function (UDF) - только встроенные функции Catalyst, поэтому преимущество 
Java в производительности не проявляется: обе задачи выполняются за сопоставимое время.

**Когда Java/Scala объективно лучше**:

- compile-time проверка типов и безопасный рефакторинг больших кодовых баз;
- typed Dataset API - ошибки схемы ловятся до запуска;
- JVM UDF без сериализации в Python-worker - заметно быстрее тяжёлых Python UDF;
- прямой доступ к JVM-библиотекам (Kafka-клиенты, JDBC, Hadoop API);
- более строгий контроль ресурсов и памяти.

Java-версия выполняет двойную роль, - демонстрирует переносимость гексагональной архитектуры на статически 
типизированный язык и служит независимой стороной проверки паритета.

---

## Общая инфраструктура

### Структура каталога `hw08/`

```
hw08/
├── Dockerfile                  # multi-stage: jar (maven) + pyspark + tools → один образ
├── docker-compose.yaml         # master, worker-1, worker-2 + submit-java, submit-pyspark, compare
├── spark-custom.conf           # spark-defaults.conf для всех узлов (REST 6066, ресурсы)
├── rest-submit.json            # заявка для REST-сабмита Java-задачи (cluster mode)
├── .dockerignore / .gitignore
├── OTUS-DE-HW08-Solution.md    # этот файл
├── data/                       # общие данные (том ./data:/opt/spark/data)
│   ├── crime.csv
│   ├── offense_codes.csv
│   └── output/{java,pyspark}/  # витрины после прогона
├── tools/
│   └── compare_marts.py        # сравнение содержимого двух витрин
├── java_solution/              # Maven-проект (pom.xml, src/, mvnw)
└── pyspark_solution/           # пакет boston_crimes_mart + точка входа
```

### Multi-stage `Dockerfile`

- **Stage 1 (`maven:3.9-eclipse-temurin-21`)**: собирает `java_solution` → `boston-crimes-mart-1.0.0.jar`
  (зависимости кэшируются через `--mount=type=cache,target=/root/.m2`).
- **Stage 2 (`apache/spark:4.2.0-scala2.13-java21-python3-ubuntu`)**: в `/opt/spark/app` включаются
  - `/opt/spark/app/boston-crimes-mart-1.0.0.jar` - Java-задача;
  - `/opt/spark/app/boston_crimes_mart_app.py` + `/opt/spark/app/boston_crimes_mart/` - PySpark-задача
    (`spark-submit /opt/spark/app/boston_crimes_mart_app.py` кладёт `/opt/spark/app` в `sys.path[0]`,
    поэтому `import boston_crimes_mart` работает без `--py-files`);
  - `/opt/spark/app/tools/compare_marts.py` - проверка паритета решений.

Один образ запускает и Java, и PySpark. Bind-mount'ов кода в compose нет - код фиксируется на этапе сборки образа, 
поэтому **после правки Python- или Java-кода нужна пересборка**: `docker compose build`.
Для быстрой итерации можно временно примонтировать код поверх включённого в образ:

```powershell
docker compose run --rm -v "${PWD}/pyspark_solution:/opt/spark/app:ro" submit-pyspark
```

### `spark-custom.conf`

Монтируется read-only как `/opt/spark/conf/spark-defaults.conf` на всех узлах:
включён REST-сабмит мастера (порт 6066), драйвер/экзекутор 512m и 1 core,
`spark.cores.max=2`, `spark.sql.shuffle.partitions=8`.

### Сервисы compose и профили

| Сервис | Профиль | Назначение |
|---|---|---|
| `master` (spark-master) | - | standalone-мастер + REST 6066 + UI 8080 |
| `worker-1` (spark-worker-1) | - | воркер, 2 cores / 2g, UI 8081 |
| `worker-2` (spark-worker-2) | - | воркер, 2 cores / 2g, UI 8082 |
| `submit-java` | `submit` | one-shot spark-submit Java-задачи (client mode) |
| `submit-pyspark` | `submit` | one-shot spark-submit PySpark-задачи (client mode) |
| `compare` | `submit` | сравнение витрин в `local[2]` (не требует кластера) |

Кластер поднимается обычным `docker compose up -d`. Одноразовые сервисы запускаются
**только** через `docker compose --profile submit run --rm <service>` (не `up -d`,
иначе они стартуют все разом).

| Что | Где |
|---|---|
| Web UI мастера | http://localhost:8080 |
| Web UI воркера 1 | http://localhost:8081 |
| Web UI воркера 2 | http://localhost:8082 |
| REST API сабмита | http://localhost:6066 |
| Spark master | localhost:7077 |

Тома у всех сервисов одинаковые: `./spark-custom.conf:/opt/spark/conf/spark-defaults.conf:ro`
и `./data:/opt/spark/data`.

### Подготовка (один раз)

Все команды - из папки `hw08/` в PowerShell:

```powershell
docker compose build
docker compose up -d
docker compose ps
```

В master UI (http://localhost:8080) видно 2 воркера / 4 cores.

---

## Часть 1. Java-решение (`java_solution/`)

### Структура пакетов (`ru.otus.de.hw08`)

- `BostonCrimesMartApp` - точка входа (main);
- `config/AppConfig` - record-конфигурация, `fromArgs` с дефолтами;
- `AppContext` - ручная сборка зависимостей (DI);
- `port/` - интерфейсы (порты) этапов пайплайна;
- `adapter/{io,clean,enrich,aggregate,spark}/` - реализации портов (адаптеры);
- `pipeline/CrimesMartPipeline` - оркестрация: load → clean → enrich → aggregate → write.

Дефолты `AppConfig` (рабочая директория `hw08/java_solution`): `../data/crime.csv`,
`../data/offense_codes.csv`, `../data/output/java`. В контейнере дефолты неприменимы
(`../data` от `/opt/spark` - это `/opt/data`), поэтому compose/REST всегда передают явные
абсолютные пути; исключение - запуск с `-w /opt/spark/app` (см. способ 2).

### Способ 1. One-shot сервис `submit-java` (client mode) - самый простой

```powershell
docker compose --profile submit run --rm submit-java
```

- Режим: **client** - драйвер в контейнере submit, задачи на воркерах кластера.
- Успех: в логах `Loading raw data... / Cleaning... / Enriching... / Aggregating... /
  Writing mart to /opt/spark/data/output/java... / Done.`, код возврата 0.
- Результат на хосте: `data\output\java\` (`_SUCCESS` + один `part-00000-*.snappy.parquet`).

### Способ 2. Ручной запуск через `docker exec`

```powershell
docker exec -it spark-master /opt/spark/bin/spark-submit `
  --class ru.otus.de.hw08.BostonCrimesMartApp `
  --master spark://master:7077 `
  --deploy-mode client `
  --driver-memory 512m --executor-memory 512m `
  --executor-cores 1 --total-executor-cores 2 `
  /opt/spark/app/boston-crimes-mart-1.0.0.jar `
  /opt/spark/data/crime.csv `
  /opt/spark/data/offense_codes.csv `
  /opt/spark/data/output/java
```

Вариант **без аргументов** - срабатывают дефолты `AppConfig`: рабочая директория
`/opt/spark/app`, поэтому `../data` = `/opt/spark/data`:

```powershell
docker compose exec -w /opt/spark/app master /opt/spark/bin/spark-submit `
  --class ru.otus.de.hw08.BostonCrimesMartApp `
  --master spark://master:7077 --deploy-mode client `
  /opt/spark/app/boston-crimes-mart-1.0.0.jar
```

В логах будет `Writing mart to ../data/output/java...`.

### Способ 3. REST API (cluster mode) - запуск "по-взрослому"

У standalone-мастера включён REST-сервер сабмита (порт 6066). Драйвер поднимается
**на одном из воркеров**, клиент только отправляет JSON-заявку (`rest-submit.json`)
и может опрашивать статус - соединение можно рвать.

```powershell
curl.exe -s -XPOST http://localhost:6066/v1/submissions/create `
  -H "Content-Type: application/json" --data "@rest-submit.json"
```

Ответ: `"success": true`, `"submissionId": "driver-2026…-0000"`. Статус:

```powershell
curl.exe -s http://localhost:6066/v1/submissions/status/<submissionId>
```

`driverState`: `RUNNING` → `FINISHED` (или `FAILED`/`ERROR`). Реальный прогон дал
`FINISHED` с выводом витрины в `/opt/spark/data/output/java`.

Логи драйвера - на воркере из полей `workerId`/`workerHostPort` статуса:

```powershell
docker exec spark-worker-1 sh -c "tail -n 100 /opt/spark/work/driver-*/stdout"
docker exec spark-worker-2 sh -c "tail -n 100 /opt/spark/work/driver-*/stdout"
```

Также: master UI → вкладка Completed Drivers → Logs. Убить/почистить:

```powershell
curl.exe -s -XPOST http://localhost:6066/v1/submissions/kill/<submissionId>
curl.exe -s -XPOST http://localhost:6066/v1/submissions/clear
```

Нюансы:

- в PowerShell надо писать именно `curl.exe` (голый `curl` - алиас `Invoke-WebRequest`);
- `rest-submit.json` должен быть UTF-8 **без BOM**, иначе `400 Malformed request`;
- jar в заявке указан локальным путём внутри образа - работает, потому что образ общий
  для мастера и воркеров и файл лежит по одинаковому пути везде.

### Локальный запуск на хосте (без Docker)

```powershell
cd java_solution
.\mvnw.cmd clean package
spark-submit --class ru.otus.de.hw08.BostonCrimesMartApp --master "local[*]" `
  target\boston-crimes-mart-1.0.0.jar `
  ..\data\crime.csv ..\data\offense_codes.csv ..\data\output\java
```

(или вообще без аргументов - сработают дефолты `AppConfig`).

**Caveat**: на Windows для записи parquet в local mode нужны `HADOOP_HOME` и `winutils.exe`,
поэтому основной способ запуска - Docker.

---

## Часть 2. PySpark-решение (`pyspark_solution/`)

### Структура

- `boston_crimes_mart_app.py` - точка входа (`main(argv)`, logging, контекст-менеджер);
- пакет `boston_crimes_mart`:
  - `config.py` - `AppConfig` (`@dataclass(frozen=True, slots=True)`, argparse-флаги
    `--crimes_path/--codes_path/--output_path`, дефолты вычисляются от `__file__`);
  - `ports.py` - протоколы (порты) этапов;
  - `pipeline.py` - оркестрация load → clean → enrich → aggregate → write;
  - `context.py` - `AppContext`, контекст-менеджер (автоматический `spark.stop()`);
  - `adapters/{io,clean,enrich,aggregate,spark}.py` - реализации портов.

Питонические отличия от Java: argparse-флаги вместо позиционных аргументов,
frozen dataclass вместо record, контекст-менеджер вместо try/finally, `logging` вместо
slf4j, композиция адаптеров через `functools`/duck-typing.

### Запуск в кластере

```powershell
docker compose --profile submit run --rm submit-pyspark
```

Логи: `Loading raw data... / Cleaning... / Enriching... / Aggregating... /
Writing mart to /opt/spark/data/output/pyspark... / Done.`, exit code 0.
Результат на хосте: `data\output\pyspark\`.

### Локальный запуск в `.venv`

```powershell
cd pyspark_solution
.venv\Scripts\python boston_crimes_mart_app.py
```

Дефолты от `__file__` дают `../data` и `../data/output/pyspark`. Тот же caveat про
Windows/`HADOOP_HOME`/`winutils.exe`.

---

## Паритет витрин

Скрипт `tools/compare_marts.py` (включён в образ) сравнивает **содержимое** двух реализаций:

1. схемы: список `(имя колонки, тип)` должен совпадать;
2. число строк в обеих витринах;
3. full outer join по `district` - районы, присутствующие только с одной стороны, считаются разницей;
4. для общих районов: `crimes_total`, `crimes_monthly` (long) и `frequent_crime_types` (string) -
   точное равенство; `lat`, `lng` (double) - `|java - pyspark| <= 1e-9`.

Запуск (кластер не нужен, режим `local[2]`, нужен только смонтированный `./data`):

```powershell
docker compose --profile submit run --rm compare
```

### Фактический вывод прогона

```text
Schema check OK: [('district', 'string'), ('crimes_total', 'bigint'), ('lat', 'double'), ('lng', 'double'), ('crimes_monthly', 'bigint'), ('frequent_crime_types', 'string')]
Row counts: java=12 pyspark=12

district   | crimes_total j/p   | crimes_monthly j/p   | frequent_crime_types j/p                 | lat diff   | lng diff   | MATCH
-----------------------------------------------------------------------------------------------------------------------------------
A1         | 32294/32294        | 827/827              | PROPERTY, ASSAULT SIMPLE, DRUGS/PROPERTY, ASSAULT SIMPLE, DRUGS | 0.00e+00   | 0.00e+00   | OK
A15        | 6170/6170          | 156/156              | INVESTIGATE PERSON, M/V ACCIDENT, M/V/INVESTIGATE PERSON, M/V ACCIDENT, M/V | 0.00e+00   | 0.00e+00   | OK
A7         | 13024/13024        | 335/335              | SICK/INJURED/MEDICAL, INVESTIGATE PERSON, DRUGS/SICK/INJURED/MEDICAL, INVESTIGATE PERSON, DRUGS | 0.00e+00   | 0.00e+00   | OK
B2         | 46202/46202        | 1199/1199            | VERBAL DISPUTE, SICK/INJURED/MEDICAL, INVESTIGATE PERSON/VERBAL DISPUTE, SICK/INJURED/MEDICAL, INVESTIGATE PERSON | 0.00e+00   | 0.00e+00   | OK
B3         | 33700/33700        | 875/875              | VERBAL DISPUTE, INVESTIGATE PERSON, MISSING PERSON/VERBAL DISPUTE, INVESTIGATE PERSON, MISSING PERSON | 0.00e+00   | 0.00e+00   | OK
C11        | 40874/40874        | 1069/1069            | SICK/INJURED/MEDICAL, M/V, INVESTIGATE PERSON/SICK/INJURED/MEDICAL, M/V, INVESTIGATE PERSON | 0.00e+00   | 0.00e+00   | OK
C6         | 21752/21752        | 558/558              | DRUGS, SICK/INJURED/MEDICAL, INVESTIGATE PERSON/DRUGS, SICK/INJURED/MEDICAL, INVESTIGATE PERSON | 0.00e+00   | 0.00e+00   | OK
D14        | 19118/19118        | 480/480              | TOWED MOTOR VEHICLE, SICK/INJURED/MEDICAL, M/V/TOWED MOTOR VEHICLE, SICK/INJURED/MEDICAL, M/V | 0.00e+00   | 0.00e+00   | OK
D4         | 38395/38395        | 1011/1011            | LARCENY SHOPLIFTING, PROPERTY, LARCENY THEFT FROM BUILDING/LARCENY SHOPLIFTING, PROPERTY, LARCENY THEFT FROM BUILDING | 0.00e+00   | 0.00e+00   | OK
E13        | 16599/16599        | 421/421              | SICK/INJURED/MEDICAL, DRUGS, M/V ACCIDENT/SICK/INJURED/MEDICAL, DRUGS, M/V ACCIDENT | 0.00e+00   | 0.00e+00   | OK
E18        | 16639/16639        | 424/424              | SICK/INJURED/MEDICAL, INVESTIGATE PERSON, M/V/SICK/INJURED/MEDICAL, INVESTIGATE PERSON, M/V | 0.00e+00   | 0.00e+00   | OK
E5         | 12804/12804        | 328/328              | SICK/INJURED/MEDICAL, INVESTIGATE PERSON, M/V/SICK/INJURED/MEDICAL, INVESTIGATE PERSON, M/V | 0.00e+00   | 0.00e+00   | OK

PARITY OK: 12 districts, 0 differences
```

Почему не сравниваю байты или хэши part-файлов? Имя файла содержит случайный UUID,
генерируемый при записи, а порядок строк после shuffle не гарантирован контрактом Spark.
Байт-идентичность недостижима без искусственной сортировки перед записью, поэтому
критерий паритета - содержимое: схема, число строк, состав районов и значения полей
(double - с допуском 1e-9).

---

## Проверка результата руками

```powershell
dir .\data\output\java
dir .\data\output\pyspark
```

Чтение витрин через `spark-shell` в контейнере:

```powershell
@'
spark.read.parquet("/opt/spark/data/output/java").printSchema()
spark.read.parquet("/opt/spark/data/output/java").show(false)
spark.read.parquet("/opt/spark/data/output/pyspark").show(false)
:quit
'@ | docker compose exec -T master /opt/spark/bin/spark-shell --master "local[1]"
```

---

## Остановка и чистка

```powershell
docker compose stop
docker compose --profile submit down --remove-orphans
docker image rm boston-crimes-mart:spark-4.2.0-java21-python3
```
