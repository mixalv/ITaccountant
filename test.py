import requests

url = f"https://bank.gov.ua/NBUStatService/v1/statdirectory/exchangenew?valcode=USD&date=20210222&json"
response = requests.get(url)
response = response.json()

print(response)
print(response[0]['rate'])