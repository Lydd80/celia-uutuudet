#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# moduuli komentoriviparametrien käsittelyyn
import argparse
import time
import os
import logging

# luokka uutuusluetteloiden käsittelyyn
from uutuusluettelo import Uutuusluettelo
# luokka kirjanpitämiseen edellisen luettelon luontikerran kirjoista
from kasitellyt import Käsitellyt
# luokka luetteloiden lähettämiseen sähköpostilla
from posti import Postittaja

def kysyPostitetaanko( luettelo ):
    '''Postitus vaiheessa käytettävä funktio
    
    Jos käyttäjä määrittää komentoriviparametrilla, että häneltä kysytään postitetaanko luettelot,
    käytetään tätä funktiota käyttäjältä luvan kysymiseen jokaisen luettelon postituksesta.'''
    # käyttäjän vastaus kysymykseen
    vastaus = ''
    # kysytään kunnes käyttäjä vastaa k tai e
    while vastaus not in [ 'k', 'e' ]:
        vastaus = input( 'Lähetetäänkö ' +luettelo['tiedosto'] + ' sähköpostilla. Vastaa k tai e: ' )
        
    return vastaus == 'k'


### def wrapStringInHTMLMac(program, url, body):
###   import datetime
###    from webbrowser import open_new_tab
###
###    now = datetime.datetime.today().strftime("%Y%m%d-%H%M%S")
###    filename = program + '.html'
###    f = open(filename,'w')
###
###   wrapper = """<html>
###    <head>
###    <title>%s output - %s</title>
###   </head>
###   <body><p>URL: <a href=\"%s\">%s</a></p><p>%s</p></body>
###    </html>"""
###    whole = wrapper % (program, now, url, url, body)
###    f.write(whole)
###    f.close()
###

# määritetään ohjelman komentorivi parametrit    
komentorivi = argparse.ArgumentParser()
# määritetään -p valitsin, jolla valitaan miten luetteloiden sähköpostilla lähetyksen kanssa toimitaan
komentorivi.add_argument( '-p', '--posti', 
                          choices =  [ 'kyllä', 'ei', 'kysy', 'heti' ],
                          default = 'ei',
                          help = 'Määrittele miten luettelot postitetaan' )
# käsitellään komentoriviparametrit
parametrit = komentorivi.parse_args()

# hakemisto josta ohjelman tiedostot luetaan. Hakemisto on tämän koodi tiedoston hakemisto.
hakemisto = os.path.dirname( os.path.abspath( __file__ )) +'/'

# määritellään ohjelma kirjoittamaan tulosteitaan konsolille ja tiedostoon
# käytetään logging moduulia. Luodaan Logger olio, jota
# käytetään tulosteiden kirjoittamiseen. Määritetään käsittelijät (handler) kirjoitamaan tiedostoon ja konsolille.
loki = logging.getLogger( 'celia-uutuudet' )
# tulostetaan kaikki mahdolliset loki viestit
loki.setLevel( logging.DEBUG )
konsoliKäsittelijä = logging.StreamHandler()
loki.addHandler( konsoliKäsittelijä )
tiedostoKäsittelijä = logging.FileHandler( hakemisto +'uutuushaku.log', encoding = 'utf-8' )
# oletuksena konsolille tulostuu vain viesti. Tiedostoon haluamme myös ajan ja tyypin.
# Tulostettavan viestin muoto määritellään Formatter oliolla
muotoilija = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
tiedostoKäsittelijä.setFormatter( muotoilija )
loki.addHandler( tiedostoKäsittelijä )

# napataan ohjelman suorituksen aikana syntyvät odottamattomat poikkeukset
try:
    # määritetään mitä uutuusluetteloita käsitellään
    # luettelosta määritetään osoite mistä uutuudet löytyvät
    # tiedosto, johon ne tallennetaan,  luettelon nimi ja luokka, jonka instanssilla luettelo käsitellään
    luettelot = [
        {
            'url': 'https://www.celianet.fi/kirjavinkit/uutuuskirjat-aikuisille/',
            'otsikko': 'Aikuisten uutuudet',
            'tiedosto': 'aikuisten_uutuudet.txt',
            'luettelo': Uutuusluettelo
        },
        {
            'url': 'https://www.celianet.fi/kirjavinkit/lasten-uutuuskirjat/',
            'otsikko': 'Lasten ja nuorten uutuudet',
            'tiedosto': 'lasten_ja_nuorten_uutuudet.txt',
            'luettelo': Uutuusluettelo
        }
    ]
    
    # jos käyttäjä haluaa postittaa aikaisemmin luodut luettelot ei luoda niitä nyt
    if parametrit.posti != 'heti':
        # olio, josta luetaan edellisen luettelon luonti kerran uusimmat kirjat eri kategorioista, joita vanhempia
        # kirjoja ei lisätä nyt luotaviin luetteloihin.
        # tähän myös tallennetaan tällä hetkellä uusimmat kirjat eri kategorioista, jolloin niitä ei luetteloida ensi kerralla
        # tiedot luetaan ja tallennetaan json muodossa vanhat.json tiedostoon
        vanhat = Käsitellyt( hakemisto +"vanhat.json" )
        # käsitellään jokainen luettelo
        loki.info( 'luodaan luetteloita.' )
        for luettelo in luettelot:
            # luodaan luettelon käsittely luokasta instanssi, jolle annetaan osoite, josta luettelo löytyy, nimi tiedostolle, johon uutuudet tallennetaan,  tiedot käsitellyistä kirjoista, 
            # sekä hakemisto luettelotiedostolle
            hakija = luettelo['luettelo']( luettelo['url'], luettelo['tiedosto'], vanhat, hakemisto )
            # haetaan kirjat ja tallennetaan tiedostoon
            hakija.haeKirjat()
            
        # tallennetaan tämän luettelon eri kategorioiden uusimmat seuraavaa kertaa varten    
        vanhat.tallenna()
    
    # postitetaan luettelot jos käyttäjä niin halusi
    if parametrit.posti in  [ 'kyllä', 'kysy', 'heti' ]:
        # luodaan postin lähettäjä konfiguraation pohjalta
        postittaja = Postittaja( hakemisto )
        # käydään luettelot läpi
        for luettelo in luettelot:
            # postitetaan luettelo heti jos käyttäjä niin halusi muuten kysytään jokaisen luettelon kohdalla haluaako käyttäjä sen lähettää
            if parametrit.posti in [ 'kyllä', 'heti' ]  or kysyPostitetaanko( luettelo ):
                loki.info( 'Postitetaan {}'.format( luettelo['otsikko'] ))
                postittaja.postita( luettelo )
                # odotetaan 5 sekuntia ennen seuraava postitusta
                # nopeasti peräkkäin lähetettävät viestit saattavat aiheuttaa ongelmia THP:n sähköpostilistoilla
                time.sleep( 5 )

except Exception as virhe:
    # kirjoitetaan odottamattoman virheen tiedot lokiin
    loki.exception( "tapahtui odottamaton virhe" ) 
