# -*- coding: utf-8 -*-

import json
import shutil

class Käsitellyt():
    """Luokka, jonka avulla pidetään kirjaa siitä, mitkä kirjat on jo edellisellä luettelon luontikerralla käsitelty
    
    Luokassa on jokaisen luettelon jokaisen kategorian uusimman kirjan id."""
    
    def __init__( self, tiedostoNimi ):
        """Luo perustuen annetun nimiseen tiedostoon, josta tiedot luetaan ja johon ne tallennetaan."""
        self.tiedostoNimi = tiedostoNimi
        try:
            # yritä lukea tiedot JSON muodossa tiedostosta
            tiedosto = open( tiedostoNimi, 'r', encoding = 'utf-8' )
            # luokan sisällä käsitellään tietoja python sanakirjana
            self.vanhat = json.load( tiedosto )
            tiedosto.close()
            
        except FileNotFoundError:
            # ei tiedostoa lähdetään liikkeelle tyhjällä sanakirjalla
            self.vanhat = {}
            
        except json.decoder.JSONDecodeError:
            print( 'Käsiteltyjen kirjojen tiedoston lukeminen epäonnistui: ei validi json tiedosto.' )
            quit()
            
    def lisää( self, luetteloNimi, kategoria, kirjaId ):
        """Lisää kirjaID liittyen tietyn luettelon tiettyyn kategoriaan."""
        luettelo = self.vanhat.get( luetteloNimi )
        if luettelo == None:
            # annettuun luetteloon ei vielä ole tietoja
            luettelo = {}
            self.vanhat[luetteloNimi] = luettelo
        
        luettelo[kategoria] = kirjaId
        
    def hae( self, luetteloNimi, kategoria ):
        """Hae kirjaId annetun luettelon annetun kategorian uusimmalle kirjalle viime luettelo kerralta."""
        luettelo = self.vanhat.get( luetteloNimi )
        if luettelo == None:
            return None
            
        return luettelo.get( kategoria )
        
    def tallenna( self ):
        """Tallenna tämän hetkiset tiedot tiedostoon.
        
        Luo myös kopion tiedostosta, josta tämä olio uotiin. Alkuperäinen tiedosto ylikirjoitetaan."""
        try:
            # tehdään kopio tiedostosta
            shutil.copyfile( self.tiedostoNimi, 'edelliset_' +self.tiedostoNimi )
            
        except FileNotFoundError:
            # tiedostoa ei ollut
            pass
            
        tiedosto = open( self.tiedostoNimi, 'w', encoding = 'utf-8' )
        json.dump( self.vanhat, tiedosto, ensure_ascii = False, indent = 4  )
        tiedosto.close()