from bs4 import BeautifulSoup
from time import sleep, time
import pandas as pd
import os
import shutil
import re
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

class AirbnbScrap:
    def __init__(self, destination:str, location:str, nb_pers:int, mois_resa:int, 
                annee_resa:int, prix_brut:int, piscine:int, nb_chambres:int) -> None:
        self.destination = destination
        self.location = location
        self.nb_pers = nb_pers
        self.mois_resa = mois_resa
        self.annee_resa = annee_resa
        self.prix_brut = prix_brut
        self.piscine = piscine
        self.nb_chambres = nb_chambres
        self.urlsBase = []
        self.urlFileName = "URLS"
        self.pagesFolderName = "RentalData"
        self.result = pd.DataFrame(columns=["Logement", "Prix par nuit (€)", "Réduction", "Note sur 5", 
                                        "Nb commentaires","Description", "Localisation", "Piscine"])

    #Pour avoir les 4 urls de recherches
    def get_urlsBase(self, jour_resa:str, jour_depart:str):
        '''
        les jours en format : "04", "08"
        '''    
        for _ in range(4):
            start_date = self.annee_resa +"-"+ self.mois_resa + "-" + jour_resa
            end_date = self.annee_resa + "-" + self.mois_resa + "-"+ jour_depart

            url = f"https://www.airbnb.fr/s/{self.destination}--{self.location}/homes?" \
                f"tab_id=home_tab" \
                f"&refinement_paths%5B%5D=%2Fhomes" \
                f"&flexible_trip_lengths%5B%5D=one_week" \
                f"&monthly_start_date={start_date}" \
                f"&monthly_length=3" \
                f"&price_filter_input_type=0" \
                f"&price_filter_num_nights=5" \
                f"&channel=EXPLORE" \
                f"&query=Seminyak%2C%20Bali%2C%20Indon%C3%A9sie" \
                f"&place_id=ChIJ_8h84N9G0i0R0P2CyvsLAwU" \
                f"&date_picker_type=calendar" \
                f"&checkin={start_date}" \
                f"&checkout={end_date}" \
                f"&adults={self.nb_pers}" \
                f"&source=structured_search_input_header" \
                f"&search_type=autocomplete_click"

            self.urlsBase.append(url)
            
            #rajoute 6 jours pour bien voir dans 1 mois 4 différentes dates espacés pour essayer de prendre le plus de villas possible
            jour_resa = str(int(jour_resa) + 5)
            jour_depart = str(int(jour_depart) + 5)
        


    # Si on veut avoir qu'un url de recherche

    def set_urlsBase(self, url):
        self.urlsBase = [url]

    def getAllUrls(self):
        start = time()
        url_list = []
        count = 0
        for urlBase in self.urlsBase:
            while True:
                r = requests.get(urlBase)
                if r.ok:
                    count+=1
                    print(r, count)
                    soup = BeautifulSoup(r.content, features="html.parser")
                    urls = soup.find_all(attrs={'class': 'l1ovpqvx bn2bl2p dir dir-ltr'})
                    for url in urls:
                        url_list.append('https://www.airbnb.fr' + url['href'])
                    suite = soup.find('a', {'class': 'l1ovpqvx c1ytbx3a dir dir-ltr', 'aria-label': 'Suivant'})
                    if suite is None:
                        break
                    else :
                        urlBase = 'https://www.airbnb.fr' + suite['href']
                        sleep(1)               
                else : 
                    print(f'Erreur {r}')
                    break

        # Enregistrement des urls 

        with open(f'{self.urlFileName}.txt', 'w') as f:
            for url in url_list:
                f.write(url + '\n')

        end = time()
        print("\n"+f"Temps d'éxécution : {end-start}")


    def clean_urls(self):
        # suppression des doublons ou plus
        urls_uniques = {}
        pattern_id1 = re.compile(r'/rooms/plus/(\d+)')
        pattern_id2 = re.compile(r'/rooms/(\d+)')
        with open(f'{self.urlFileName}.txt', 'r') as f:
            for row in f:
                url = row.strip()

                match1 = re.search(pattern_id1, url)
                match2 = re.search(pattern_id2, url)


                if match1:
                    id = match1.group(1)
                        
                    # Vérifier si l'ID est déjà présent dans le dictionnaire
                    if id not in urls_uniques:
                        # Ajouter l'URL avec l'ID unique au dictionnaire
                        urls_uniques[id] = url
                elif match2:
                    id = match2.group(1)
                    # Vérifier si l'ID est déjà présent dans le dictionnaire
                    if id not in urls_uniques:
                        # Ajouter l'URL avec l'ID unique au dictionnaire
                         urls_uniques[id] = url
        with open(f'{self.urlFileName}.txt', 'w') as f:
            for url_unique in urls_uniques.values():
                f.write(url_unique + "\n")


    # Récupération des pages avec Selenium

    def getPages(self):
        start = time()
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options)
        pages = []
        with open(f'{self.urlFileName}.txt', 'r') as f:
            for i, row in enumerate(f):
                url = row.strip()
                try:
                    print(i+1)
                    driver.get(url)
                    sleep(6)
                    pages.append(driver.page_source.encode('utf-8'))
                except Exception as e:
                    print(f"Erreur lors du chargement de la page {url}: {str(e)}")
        driver.quit()

        # enregistrement des pages

        if os.path.exists(self.pagesFolderName):
            shutil.rmtree(self.pagesFolderName)
        os.makedirs(self.pagesFolderName, exist_ok=True)
        for page_nb, page in enumerate(pages):
            with open(f"Rental_Data/page_{page_nb+1}.html", "wb") as f_out:
                f_out.write(page)
        end = time()
        print("\n"+f"Temps d'éxécution : {end-start}")
        

    def clean_price(self, tag):
        reduction = "Non"
        if "initialement" in tag:
            reduction = "Oui"
        prix = int(tag[0:2])
        return prix, reduction
            
    def clean_note(self, tag):
        return float(tag.replace(",", ".")[0:4].strip())

    def clean_comment(self, tag):
        num =""
        for i in tag:
            if i.isdigit():
                num+=i
            else: break
        return int(num)
        
    def parse_pages(self):
        """Parse all pages from the data folder
        Returns:
            pd.DataFrame: parsed data
        """
        
        pages_paths = os.listdir(self.pagesFolderName)

        for i, pages_path in enumerate(pages_paths):
            with open(os.path.join(self.pagesFolderName, pages_path), "rb") as f_in:
                page = f_in.read().decode("utf-8")
                soup = BeautifulSoup(page, "html.parser")

                h1 = soup.find('h1', class_='hpipapi i1pmzyw7 dir dir-ltr')
                self.result.loc[i, "Logement"] = h1.text.strip()


                spans = soup.findAll('span', attrs={"class": "a8jt5op dir dir-ltr"})
                self.result.loc[i, "Prix par nuit (€)"], self.result.loc[i, "Réduction"] = self.clean_price(spans[6].text.strip())

                lilDescription = soup.find('h2', attrs={'class': 'hpipapi dir dir-ltr'}).text.strip()
                self.result.loc[i, "Description"] = lilDescription
                try:
                    note = self.clean_note(soup.find('span', attrs={"class": "_17p6nbba"}).text.strip())
                    nb_comment = self.clean_comment(soup.find('button', attrs={"class": "l1ovpqvx bbkw4bl c1rxa9od dir dir-ltr"}).text.strip())
                    self.result.loc[i, "Note sur 5"] = note
                    self.result.loc[i, "Nb commentaires"] = nb_comment
                except:
                    pass

                loc = soup.find('span', attrs={"class": "_9xiloll"})
                self.result.loc[i, "Localisation"] = loc.text.strip()
                    

                h3 = soup.find_all('h3',attrs={'class': 'hpipapi dir dir-ltr'})
                for j, h3 in enumerate(h3):   
                    if "2023" in h3.text.strip() or j==3:
                        break
                    if h3.text.strip() == "Offrez-vous un plongeon":
                        self.result.loc[i, "Piscine"] = 1
                        break
                    else :           
                        div = soup.find_all('div',attrs={'class': 'iikjzje i10xc1ab dir dir-ltr'})
                        for d in div:
                            if "piscine" in d.text.strip().lower():
                                self.result.loc[i, "Piscine"] = 1
                                break_outer = True
                                break
                            else: self.result.loc[i, "Piscine"] = 0
                        if break_outer in locals():
                            break
                                
        
# Villas étudié
destination = "Bali"
location = "Seminyak--Kabupaten-Badung"
nb_pers = "4"
mois_resa = "08"
annee_resa = "2023"
prix_brut = 100
piscine = 1
nb_chambres = 4

bnb = AirbnbScrap(destination, location, nb_pers, mois_resa, annee_resa, prix_brut, piscine, nb_chambres)

bnb.parse_pages()

print(bnb.result.head())

bnb.result.to_csv('test1.csv', index=False)






