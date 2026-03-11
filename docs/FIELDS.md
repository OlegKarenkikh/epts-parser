# FIELDS.md — Описание полей VehiclePassportData

| Поле | Тип | Описание (рус.) | Пример значения |
|---|---|---|---|
| `epts_number` | `Optional[str]` | Номер ЭПТС | `111222333444555` |
| `vin` | `Optional[str]` | Идентификационный номер (VIN) | `XTA21099071234567` |
| `pts_number` | `Optional[str]` | Номер ПТС | `77 УУ 123456` |
| `brand` | `Optional[str]` | Марка | `LADA (ВАЗ)` |
| `model` | `Optional[str]` | Коммерческое наименование | `GRANTA` |
| `vehicle_type` | `Optional[str]` | Наименование (тип) ТС | `Легковой автомобиль` |
| `category` | `Optional[str]` | Категория ТС | `B` |
| `year` | `Optional[str]` | Год изготовления | `2021` |
| `color` | `Optional[str]` | Цвет | `Белый` |
| `body_number` | `Optional[str]` | Номер кузова | `XTA21099071234567` |
| `chassis_number` | `Optional[str]` | Номер шасси | `отсутствует` |
| `country_of_manufacture` | `Optional[str]` | Страна изготовления | `Россия` |
| `engine_number` | `Optional[str]` | Номер двигателя | `12345A` |
| `engine_type` | `Optional[str]` | Тип двигателя | `ВАЗ-11183` |
| `engine_power_kw` | `Optional[str]` | Мощность двигателя (кВт) | `77.0` |
| `engine_power_hp` | `Optional[str]` | Мощность двигателя (л.с.) | `104.7` |
| `engine_volume` | `Optional[str]` | Рабочий объём двигателя | `1596` |
| `fuel_type` | `Optional[str]` | Тип топлива | `Бензин` |
| `eco_class` | `Optional[str]` | Экологический класс | `5` |
| `max_mass` | `Optional[str]` | Разрешённая максимальная масса | `1570` |
| `curb_mass` | `Optional[str]` | Масса без нагрузки | `1085` |
| `seats_count` | `Optional[str]` | Количество мест | `5` |
| `manufacturer_name` | `Optional[str]` | Наименование изготовителя | `АО «АВТОВАЗ»` |
| `manufacturer_inn` | `Optional[str]` | ИНН изготовителя | `6320000800` |
| `manufacturer_country` | `Optional[str]` | Страна нахождения изготовителя | `Россия` |
| `otts_number` | `Optional[str]` | Номер одобрения типа | `РОСС RU.АЯ46.А12345` |
| `otts_date` | `Optional[str]` | Дата одобрения типа | `01.01.2018` |
| `customs_declaration` | `Optional[str]` | Таможенная декларация | `не требуется` |
| `owner_name` | `Optional[str]` | Наименование владельца | `ООО «Ромашка»` |
| `owner_inn` | `Optional[str]` | ИНН владельца | `7700000001` |
| `owner_ogrn` | `Optional[str]` | ОГРН владельца | `1027700132195` |
| `owner_address` | `Optional[str]` | Адрес владельца | `г. Москва, ул. Ленина, д. 1` |
| `issue_date` | `Optional[str]` | Дата выдачи | `15.03.2021` |
| `issuer` | `Optional[str]` | Кем выдан | `МРЭО ГИБДД №1` |
| `raw_tables` | `list` | Сырые таблицы из PDF (не выводится) | — |
