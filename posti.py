# -*- coding: utf-8 -*-

from email.mime.text import MIMEText
import smtplib
import json
import socket
import logging

# logger lokin kirjoitusta varten
loki = logging.getLogger( 'celia-uutuudet' )

# konfiguraatio tiedoston nimi
KONFIGURAATIO_TIEDOSTO = 'posti.json'

# Luettelon alkuun liitettävä teksti
alku = '''Tämä luettelo on luotu ja lähetetty automaattisesti, joten se saattaa sisältää virheitä. Luettelon luomiseen käytetyn ohjelman lähdekoodi on saatavissa osoitteessa:
https://github.com/ohylli/celia-uutuudet

'''

class Postittaja():
    """Luokka uutuusluetteloiden lähettämiseen sähköpostilla."""
    
    def __init__( self, hakemisto ):
        '''Luo Postittaja posti.json konfiguraatio tiedoston määräämillä asetuksilla. Konfiguraatio ja luettelot luetaan annetusta hakemisto polku merkkijonosta.'''
        self.hakemisto = hakemisto
        # lue konfiguraatio tiedostosta ja muunna json python sanakirjaksi
        try:
            with open( self.hakemisto +KONFIGURAATIO_TIEDOSTO, 'r', encoding = 'utf-8' ) as tiedosto:
                konfiguraatio = json.load( tiedosto )
        
        except FileNotFoundError:
            loki.error( 'Postittajan konfiguraatio tiedostoa {} ei löytynyt.'.format( KONFIGURAATIO_TIEDOSTO ))
            quit()
            
        except json.decoder.JSONDecodeError as virhe:
            loki.error( 'Virhe postittajan konfiguraatio tiedoston käsittelyssä: ' +str( virhe ))
            quit()
        
        try:
            # tallenna konfiguraation sisältö muuttujiin
            self.lähettäjä = konfiguraatio[ 'lähettäjä' ]
            self.vastaanottajat = konfiguraatio[ 'vastaanottajat' ]
            if 'piilo_vastaanottajat' in konfiguraatio:
                self.piiloVastaanottajat = konfiguraatio[ 'piilo_vastaanottajat' ]
            
            else:
                self.piiloVastaanottajat = None
            
            self.palvelinNimi = konfiguraatio['palvelin']
            self.portti = konfiguraatio[ 'portti' ]
            self.käyttäjä = konfiguraatio[ 'käyttäjä' ]
            self.salasana = konfiguraatio[ 'salasana' ]
            
        except KeyError as virhe:
            loki.error( '{} puuttuu postittajan konfiguraatiotiedostosta.'.format( virhe.args[0] ))
            quit()
            
    def luoPostiPalvelin( self ):
        '''Luo ja palauta SMTP palvelinasiakas luettelon lähetystä varten  konfiguraatiotiedoston asetusten pohjalta.'''
        # Luo asiakas sähköpostipalvelimelle, joka on määritelty konfiguraatiotiedostossa
        # käytetään heti SSL salattua yhteyttä
        # ainakin soneran palvelin mail.inet.fi vaatii heti salatun yhteyden eli ei voida luoda salaamatonta asiakasta ja sitten käynnistää salattua yhteyttä
        try:
            palvelin = smtplib.SMTP_SSL( self.palvelinNimi, self.portti )
            # kirjaudutaan palvelimelle konfiguraatiossa olleilla käyttäjätunnuksella ja salasanalla
            palvelin.login( self.käyttäjä, self.salasana )
            return palvelin
            
        except ConnectionRefusedError:
            loki.error( 'Postipalvelin kieltäytyi yhteydestä. Portti voi olla väärä.' )
            quit()
            
        except socket.gaierror:
            loki.error( 'Yhteys postipalvelimeen epäonnistui. Tarkista, että palvelimen osoite on oikea.' )
            quit()
            
        except smtplib.SMTPAuthenticationError:
            loki.error( 'Kirjautuminen postipalvelimelle ei onnistunut. Tarkista käyttäjätunnus ja salasana.' )
            quit()
        
    def postita( self, luettelo ):
        '''Postittaa parametrina saadun luettelo sanakirjan määrittämän uutuusluettelon.'''
        # luetaan uutuusluettelon sisältö tiedostosta
        try:
            with open( self.hakemisto +luettelo['tiedosto'], 'r', encoding = 'utf-8' ) as tiedosto:
                runko = tiedosto.read()
                
        except FileNotFoundError:
                loki.error( 'Postittaja ei löytänyt luettelotiedostoa {}.'.format( luettelo['tiedosto'] ))
                return
                
        if len( runko ) == 0:
            loki.info( 'Luettelo {} on tyhjä eikä sitä postiteta.'.format( luettelo['tiedosto'] ))
            return
            
        # luodaan tekstimuotoinen lähetettävä viesti, jonka rungoksi asetetaan luettelon sisältö
        viesti = MIMEText( alku +runko, 'plain' )
        # asetetaan viestin lähettäjä
        viesti['From'] = self.lähettäjä
        # asetetaan vastaanottajat. Yhdistetään vastaanottaja listan osoitteet yhdeksi merkkijonoksi pilkulla eroteltuna
        viesti['To'] = ','.join( self.vastaanottajat )
        # Jos on määritelty Bcc eli piilotetut vastaanottajat lisätään ne
        if self.piiloVastaanottajat != None:
            viesti['Bcc'] = ','.join( self.piiloVastaanottajat )
            
        # asetetaan viestin otsikoksi luettelon otsikko
        viesti['Subject'] = luettelo['otsikko']
        # luodaan SMTP palvelinyhteys luettelon lähetystä varten
        palvelin =  self.luoPostiPalvelin()
        # lähetetään viesti
        palvelin.send_message( viesti )