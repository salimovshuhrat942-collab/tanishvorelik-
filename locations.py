# locations.py
# O'zbekiston Respublikasi hududiy tuzilishi: 12 viloyat + Qoraqalpog'iston Respublikasi + Toshkent shahri

REGIONS = {
    "Toshkent shahri": [
        "Bektemir", "Chilonzor", "Yakkasaroy", "Mirzo Ulug'bek", "Mirobod",
        "Olmazor", "Sergeli", "Shayxontohur", "Uchtepa", "Yashnobod",
        "Yunusobod", "Yangihayot",
    ],
    "Toshkent viloyati": [
        "Bekobod", "Bo'ka", "Chinoz", "Qibray", "Ohangaron", "Oqqo'rg'on",
        "Parkent", "Piskent", "Quyi Chirchiq", "O'rta Chirchiq",
        "Yuqori Chirchiq", "Yangiyo'l", "Zangiota", "Nurafshon",
    ],
    "Andijon viloyati": [
        "Andijon shahar", "Asaka", "Baliqchi", "Bo'z", "Buloqboshi",
        "Izboskan", "Jalaquduq", "Xo'jaobod", "Qo'rg'ontepa", "Marhamat",
        "Oltinko'l", "Paxtaobod", "Shahrixon", "Ulug'nor", "Xonobod",
    ],
    "Farg'ona viloyati": [
        "Farg'ona shahar", "Marg'ilon", "Qo'qon", "Beshariq", "Bog'dod",
        "Buvayda", "Dang'ara", "Furqat", "Farg'ona tumani", "Oltiariq",
        "Quva", "Qo'shtepa", "Rishton", "So'x", "Toshloq", "Uchko'prik",
        "O'zbekiston tumani", "Yozyovon",
    ],
    "Namangan viloyati": [
        "Namangan shahar", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq",
        "Namangan tumani", "Norin", "Pop", "To'raqo'rg'on", "Uchqo'rg'on",
        "Uychi", "Yangiqo'rg'on",
    ],
    "Sirdaryo viloyati": [
        "Guliston", "Boyovut", "Guliston tumani", "Mirzaobod", "Oqoltin",
        "Sardoba", "Sayxunobod", "Sirdaryo", "Xovos", "Shirin",
    ],
    "Jizzax viloyati": [
        "Jizzax shahar", "Arnasoy", "Baxmal", "Do'stlik", "Forish",
        "G'allaorol", "Zomin", "Zafarobod", "Zarbdor", "Mirzachul",
        "Paxtakor", "Yangiobod",
    ],
    "Samarqand viloyati": [
        "Samarqand shahar", "Bulung'ur", "Ishtixon", "Jomboy", "Kattaqo'rg'on",
        "Qo'shrabot", "Narpay", "Nurobod", "Oqdaryo", "Payariq",
        "Pastdarg'om", "Paxtachi", "Samarqand tumani", "Toyloq", "Urgut",
    ],
    "Qashqadaryo viloyati": [
        "Qarshi shahar", "Kasbi", "Kitob", "Qamashi", "Qarshi tumani",
        "Koson", "Mirishkor", "Muborak", "Nishon", "Chiroqchi",
        "Shahrisabz", "Yakkabog'", "Dehqonobod", "G'uzor",
    ],
    "Surxondaryo viloyati": [
        "Termiz shahar", "Angor", "Bandixon", "Boysun", "Denov",
        "Jarqo'rg'on", "Muzrabot", "Oltinsoy", "Qiziriq", "Qumqo'rg'on",
        "Sariosiyo", "Sherobod", "Sho'rchi", "Uzun",
    ],
    "Buxoro viloyati": [
        "Buxoro shahar", "Kogon", "Kogon tumani", "Vobkent", "G'ijduvon",
        "Jondor", "Peshku", "Qorako'l", "Qorovulbozor", "Romitan",
        "Shofirkon", "Olot",
    ],
    "Navoiy viloyati": [
        "Navoiy shahar", "Zarafshon", "Konimex", "Karmana", "Qiziltepa",
        "Xatirchi", "Nurota", "Tomdi", "Uchquduq",
    ],
    "Xorazm viloyati": [
        "Urganch shahar", "Xiva", "Bog'ot", "Gurlan", "Hazorasp", "Xonqa",
        "Qo'shko'pir", "Shovot", "Urganch tumani", "Yangibozor", "Yangiariq",
    ],
    "Qoraqalpog'iston Respublikasi": [
        "Nukus shahar", "Amudaryo", "Beruniy", "Chimboy", "Ellikqal'a",
        "Kegeyli", "Mo'ynoq", "Nukus tumani", "Qanliko'l", "Qorao'zak",
        "Qo'ng'irot", "Shumanay", "Taxtako'pir", "To'rtko'l", "Xo'jayli",
    ],
}

REGION_NAMES = list(REGIONS.keys())


def get_districts(region: str):
    return REGIONS.get(region, [])
