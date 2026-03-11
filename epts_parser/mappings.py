from __future__ import annotations

# Maps Russian label patterns (regex) to VehiclePassportData field names.
# Patterns are matched case-insensitively against the stripped label cell text.
FIELD_MAPPING: dict[str, str] = {
    # --- ЭПТС number (header or table cell) ---
    r"номер\s+эптс": "epts_number",

    # --- VIN / identification number ---
    r"идентификационный\s+номер": "vin",

    # --- PTS ---
    r"номер\s+птс": "pts_number",

    # --- Brand / make ---
    r"^марка$": "brand",

    # --- Commercial name / model ---
    r"коммерческое\s+наименование": "model",

    # --- Vehicle type ---
    r"наименование\s+\(тип\)\s+тс": "vehicle_type",

    # --- Category (both short "категория ТС" and long real-PDF variant) ---
    r"категория\s+транспортного\s+средства": "category",
    r"категория\s+тс": "category",

    # --- Year ---
    r"год\s+изготовления": "year",

    # --- Color ("цвет" alone OR "цвет кузова...") ---
    r"цвет": "color",

    # --- Body / chassis / engine numbers ---
    r"номер\s+кузова": "body_number",
    r"номер\s+шасси": "chassis_number",
    r"номер\s+двигателя": "engine_number",

    # --- Country of manufacture ---
    r"страна\s+изготовления": "country_of_manufacture",

    # --- Engine type (incl. "марка, тип" in real PDF) ---
    r"тип\s+двигателя": "engine_type",
    r"двигатель\s+внутреннего\s+сгорания": "engine_type",

    # --- Engine power: "мощность двигателя" OR "максимальная мощность" ---
    r"мощность\s+двигателя": "engine_power_kw",
    r"максимальная\s+мощность": "engine_power_kw",

    # --- Engine volume: "рабочий объём" OR "рабочий объем" ---
    r"рабочий\s+объ[ёе]м": "engine_volume",

    # --- Fuel type: "тип топлива" OR "вид топлива" ---
    r"тип\s+топлива": "fuel_type",
    r"вид\s+топлива": "fuel_type",

    # --- Eco class ---
    r"экологический\s+класс": "eco_class",

    # --- Max mass: standard OR real-PDF "технически допустимая максимальная масса" ---
    r"разрешённая\s+максимальная\s+масса": "max_mass",
    r"технически\s+допустимая\s+максимальная\s+масса": "max_mass",

    # --- Curb mass: standard OR "масса транспортного средства в снаряженном" ---
    r"масса\s+без\s+нагрузки": "curb_mass",
    r"масса\s+транспортного\s+средства\s+в\s+снаряженном": "curb_mass",

    # --- Seats: "количество мест" OR "количество мест для сидения" ---
    r"количество\s+мест": "seats_count",

    # --- Manufacturer ---
    r"наименование\s+изготовителя": "manufacturer_name",
    r"изготовитель$": "manufacturer_name",
    r"инн\s+изготовителя": "manufacturer_inn",
    r"страна\s+нахождения\s+изготовителя": "manufacturer_country",
    r"адрес\s+изготовителя": "manufacturer_country",

    # --- OTTS / approval ---
    r"номер\s+одобрения\s+типа": "otts_number",
    r"документ.*соответствие": "otts_number",
    r"дата\s+одобрения\s+типа": "otts_date",

    # --- Customs ---
    r"таможенная\s+декларация": "customs_declaration",
    r"таможенный\s+приходный\s+ордер": "customs_declaration",
    r"серия.*номер.*таможен": "customs_declaration",

    # --- Owner: standard OR real-PDF "Собственник" ---
    r"наименование\s+владельца": "owner_name",
    r"^собственник$": "owner_name",
    r"инн\s+владельца": "owner_inn",
    r"огрн\s+владельца": "owner_ogrn",
    r"адрес\s+владельца": "owner_address",

    # --- Document ---
    r"дата\s+выдачи": "issue_date",
    r"дата\s+оформления": "issue_date",
    r"кем\s+выдан": "issuer",
    r"наименование\s+организации.*оформившей": "issuer",
}

# Maps English field names to Russian display labels
RU_LABELS: dict[str, str] = {
    "epts_number": "Номер ЭПТС",
    "vin": "Идентификационный номер (VIN)",
    "pts_number": "Номер ПТС",
    "brand": "Марка",
    "model": "Коммерческое наименование",
    "vehicle_type": "Наименование (тип) ТС",
    "category": "Категория ТС",
    "year": "Год изготовления",
    "color": "Цвет",
    "body_number": "Номер кузова",
    "chassis_number": "Номер шасси",
    "country_of_manufacture": "Страна изготовления",
    "engine_number": "Номер двигателя",
    "engine_type": "Тип двигатеня",
    "engine_power_kw": "Мощность двигателя (кВт)",
    "engine_power_hp": "Мощность двигателя (л.с.)",
    "engine_volume": "Рабочий объём двигателя",
    "fuel_type": "Тип топлива",
    "eco_class": "Экологический класс",
    "max_mass": "Разрешённая максимальная масса",
    "curb_mass": "Масса без нагрузки",
    "seats_count": "Количество мест",
    "manufacturer_name": "Наименование изготовителя",
    "manufacturer_inn": "ИНН изготовителя",
    "manufacturer_country": "Страна нахождения изготовителя",
    "otts_number": "Номер одобрения типа",
    "otts_date": "Дата одобрения типа",
    "customs_declaration": "Таможенная декларация",
    "owner_name": "Наименование владельца",
    "owner_inn": "ИНН владельца",
    "owner_ogrn": "ОГРН владельца",
    "owner_address": "Адрес владельца",
    "issue_date": "Дата выдачи",
    "issuer": "Кем выдан",
}
