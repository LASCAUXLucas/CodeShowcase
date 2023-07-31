import requests
from bs4 import BeautifulSoup
import pandas as pd



def scrape_calendar_data(url):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        calendar_data = []

        event_rows = soup.find_all('tr', class_='calendar__row')

        for event_row in event_rows:
            date_element = event_row.find('span', class_='date')
            date = date_element.text.strip() if date_element else "Date Not Found"

            time_element = event_row.find('div', class_='calendar__time')
            time = time_element.text.strip() if time_element else "Time Not Found"

            event_element = event_row.find('span', class_='calendar__event-title')
            event = event_element.text.strip() if event_element else "Event Not Found"

            impact_element = event_row.find('span', class_='calendar__impact-icon')
            impact = impact_element['title'].replace(" Impact Expected", "") if impact_element else "Impact Not Found"

            calendar_data.append({'Date': date, 'Time': time, 'Event': event, 'Impact': impact})

        return calendar_data
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return []

url = 'https://www.forexfactory.com/calendar'
calendar_data = scrape_calendar_data(url)

df = pd.DataFrame(calendar_data)


print(df)
