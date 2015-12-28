import requests
import re

from cloudbot import hook
from bs4 import BeautifulSoup
from time import time

# currencies supported
currencies = [ "AED", "AFN", "ALL", "AMD", "ANG", "AOA", "ARS", "AUD", "AWG", "AZN", "BAM", "BBD", "BDT", "BGN", "BHD", "BIF", "BMD", "BND", "BOB", "BRL", "BSD", "BTC", "BTN", "BWP", "BYR", "BZD", "CAD", "CDF", "CHF", "CLF", "CLP", "CNH", "CNY", "COP", "CRC", "CUP", "CVE", "CZK", "DEM", "DJF", "DKK", "DOP", "DZD", "EGP", "ERN", "ETB", "EUR", "FIM", "FJD", "FKP", "FRF", "GBP", "GEL", "GHS", "GIP", "GMD", "GNF", "GTQ", "GYD", "HKD", "HNL", "HRK", "HTG", "HUF", "IDR", "IEP", "ILS", "INR", "IQD", "IRR", "ISK", "ITL", "JMD", "JOD", "JPY", "KES", "KGS", "KHR", "KMF", "KPW", "KRW", "KWD", "KYD", "KZT", "LAK", "LBP", "LKR", "LRD", "LSL", "LTL", "LVL", "LYD", "MAD", "MDL", "MGA", "MKD", "MMK", "MNT", "MOP", "MRO", "MUR", "MVR", "MWK", "MXN", "MYR", "MZN", "NAD", "NGN", "NIO", "NOK", "NPR", "NZD", "OMR", "PAB", "PEN", "PGK", "PHP", "PKG", "PKR", "PLN", "PYG", "QAR", "RON", "RSD", "RUB", "RWF", "SAR", "SBD", "SCR", "SDG", "SEK", "SGD", "SHP", "SKK", "SLL", "SOS", "SRD", "STD", "SVC", "SYP", "SZL", "THB", "TJS", "TMT", "TND", "TOP", "TRY", "TTD", "TWD", "TZS", "UAH", "UGX", "USD", "UYU", "UZS", "VEF", "VND", "VUV", "WST", "XAF", "XCD", "XDR", "XOF", "XPF", "YER", "ZAR", "ZMK", "ZMW", "ZWL" ]
converter  = "https://www.google.com/finance/converter?a={}&from={}&to={}"
def finance_converter(amount, ffrom, to):
    url = converter.format(amount, ffrom, to)
    params = {
        'a' : amount,
        'from': ffrom,
        'to': to
    }
    res = requests.get(url, params=params)

    if res.status_code != 200:
        return None

    soup = BeautifulSoup(res.content, 'html.parser')

    ret = soup.find("span", attrs={"class": "bld"})

    if ret == None:
        return None

    out = ''
    out += str(amount) + ' ' + ffrom + ' = ' + ret.text
    return out

@hook.command("conv")
def conv(text):
    return convert(text)

@hook.command("convert")
def convert(text):
    """
    convert [amount] <from> to <to>
    """

    # 7 eur to usd
    c1 = re.compile(r'^([0-9]+(\.[0-9]+)?)\s+([a-z]{3})\s+to\s+([a-z]{3})$', re.IGNORECASE)
    # eur 7 to usd
    c2 = re.compile(r'^([a-z]{3})\s+([0-9]+(\.[0-9]+)?)\s+to\s+([a-z]{3})$', re.IGNORECASE)
    # eur to usd
    c3 = re.compile(r'^([a-z]{3})\s+to\s+([a-z]{3})$', re.IGNORECASE)

    inp = text.upper().strip()

    r1 = re.findall(c1, inp)
    r2 = re.findall(c2, inp)
    r3 = re.findall(c3, inp)
    if len(r1):
        to     = r1[0][3]
        ffrom  = r1[0][2]
        amount = r1[0][0]
    elif len(r2):
        to     = r2[0][3]
        ffrom  = r2[0][0]
        amount = r2[0][1]
    elif len(r3):
        to     = r3[0][1]
        ffrom  = r3[0][0]
        amount = 1
    else:
        return "invalid arguments"

    if ffrom not in currencies or to not in currencies:
        return "invalid arguments"

    data = finance_converter(amount, ffrom, to)
    if not data:
        return "internal error: data not loaded"

    return data
